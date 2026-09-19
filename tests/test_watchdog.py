#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_watchdog.py
# Description: Contract tests for the hub watchdog — what it says when the RM4 Pro
#              goes quiet, when it power-cycles, and when it gives up.
# Author:      CliveS & Claude Opus 5
# Date:        19-09-2026
# Version:     1.0

from datetime import datetime, timedelta

import pytest

STAMP = "%Y-%m-%d %H:%M:%S"


def _hub(make_device, **props):
    base = {"host": "192.168.4.56", "port": "80", "heartbeatMinutes": "5"}
    base.update(props)
    return make_device(20637040, "Broadlink RM4 Pro", "rm4Pro", props=base)


def _plug(make_device):
    return make_device(814381805, "Living Room Fire Plug", "shellyRelay",
                       plugin_id="com.clives.indigoplugin.shellydirect")


# ---------------------------------------------------------------- gap wording

@pytest.mark.parametrize("minutes,expected", [
    (0,    "less than a minute"),
    (1,    "1 minute"),
    (2,    "2 minutes"),
    (59,   "59 minutes"),
    (60,   "1 hour"),
    (61,   "1 hour and 1 minute"),
    (75,   "1 hour and 15 minutes"),
    (120,  "2 hours"),
    (162,  "2 hours and 42 minutes"),
])
def test_a_gap_is_described_the_way_a_person_says_it(plugin, minutes, expected):
    now = datetime(2026, 9, 19, 21, 40, 0)
    then = (now - timedelta(minutes=minutes)).strftime(STAMP)
    assert plugin._describe_gap(then, now) == expected


def test_a_gap_never_reads_as_a_bare_number(plugin):
    now = datetime(2026, 9, 19, 21, 40, 0)
    then = (now - timedelta(minutes=162)).strftime(STAMP)
    text = plugin._describe_gap(then, now)
    assert "|" not in text and "=" not in text
    assert text.isascii()
    assert any(word in text for word in ("minute", "hour"))


def test_an_unreadable_stamp_does_not_crash_the_wording(plugin):
    now = datetime(2026, 9, 19, 21, 40, 0)
    assert plugin._describe_gap("not a date", now) == "an unknown time"
    assert plugin._describe_gap("", now) == "an unknown time"
    assert plugin._minutes_between("rubbish", now) is None


# ------------------------------------------------------------- going quiet

def test_first_miss_latches_says_it_once_and_does_not_cycle(plugin, devices, make_device, device_cmds):
    hub = devices.add(_hub(make_device, recoveryPlug="814381805", recoveryAfterMinutes="10"))
    devices.add(_plug(make_device))
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)

    assert hub.states["connectionState"] == "Unreachable"
    assert hub.states["unreachableSince"]
    assert hub.errorState == "unreachable"
    assert len(plugin.logger.lines["error"]) == 1
    assert device_cmds.calls == [], "must not cut power on a single missed probe"


def test_the_outage_is_announced_once_not_on_every_pass(plugin, devices, make_device):
    hub = devices.add(_hub(make_device))
    plugin._hub_answers = lambda dev: False
    for _ in range(5):
        plugin._check_hub(hub)
    assert len(plugin.logger.lines["error"]) == 1


def test_a_latch_written_before_a_restart_keeps_it_quiet(plugin, devices, make_device):
    # deviceStartComm re-seeds from the stored state, so the "say it once"
    # survives a plugin restart instead of resetting.
    hub = devices.add(_hub(make_device))
    hub.states["unreachableSince"] = "2026-09-19 18:58:41"
    plugin._load_codes = lambda dev=None: {}
    plugin.deviceStartComm(hub)
    assert hub.states["unreachableSince"] == "2026-09-19 18:58:41"
    assert hub.states["connectionState"] == "Unreachable"
    assert hub.errorState == "unreachable"

    plugin._hub_answers = lambda dev: False
    plugin._check_hub(hub)
    assert plugin.logger.lines["error"] == []


# --------------------------------------------------------------- recovery

def _down_for(hub, minutes, now):
    hub.states["unreachableSince"] = (now - timedelta(minutes=minutes)).strftime(STAMP)


def test_it_cuts_power_once_the_hub_has_been_missing_long_enough(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805",
                           recoveryAfterMinutes="10", recoveryOffSeconds="10"))
    devices.add(_plug(make_device))
    _down_for(hub, 12, now)
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)

    assert device_cmds.calls == [("off", 814381805, 10)]
    assert hub.states["recoveryAttempts"] == 1
    assert hub.states["lastRecoveryAt"]


def test_it_waits_for_the_threshold_before_cutting_power(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805", recoveryAfterMinutes="10"))
    devices.add(_plug(make_device))
    _down_for(hub, 4, now)
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)
    assert device_cmds.calls == []


def test_with_no_plug_chosen_it_reports_and_never_switches_anything(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="0"))
    _down_for(hub, 600, now)
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)
    assert device_cmds.calls == []
    assert hub.states["connectionState"] == "Unreachable"


def test_it_leaves_a_gap_between_attempts(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805", recoveryAfterMinutes="10"))
    devices.add(_plug(make_device))
    _down_for(hub, 30, now)
    hub.states["recoveryAttempts"] = 1
    hub.states["lastRecoveryAt"] = (now - timedelta(minutes=5)).strftime(STAMP)
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)
    assert device_cmds.calls == [], "cycling again after 5 minutes interrupts the rejoin"

    hub.states["lastRecoveryAt"] = (now - timedelta(minutes=16)).strftime(STAMP)
    plugin._check_hub(hub)
    assert device_cmds.calls == [("off", 814381805, 10)]


def test_it_stops_after_the_last_attempt_and_says_so_once(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805",
                           recoveryAfterMinutes="10", recoveryMaxAttempts="2"))
    devices.add(_plug(make_device))
    _down_for(hub, 20, now)
    hub.states["recoveryAttempts"] = 1
    hub.states["lastRecoveryAt"] = (now - timedelta(minutes=16)).strftime(STAMP)
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)            # this is attempt 2 of 2
    assert hub.states["recoveryAttempts"] == 2
    gave_up = [line for line in plugin.logger.lines["error"] if "Leaving it alone" in line]
    assert len(gave_up) == 1

    before = list(device_cmds.calls)
    for _ in range(4):
        plugin._check_hub(hub)
    assert device_cmds.calls == before, "a dead hub must not be cycled all night"
    gave_up = [line for line in plugin.logger.lines["error"] if "Leaving it alone" in line]
    assert len(gave_up) == 1, "the give-up is said once, not on every pass"


def test_a_missing_plug_is_reported_and_not_retried_blindly(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="999999999", recoveryAfterMinutes="10"))
    _down_for(hub, 20, now)
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)
    assert device_cmds.calls == []
    assert any("no longer exists" in line for line in plugin.logger.lines["error"])


def test_a_failed_switch_command_is_logged_and_not_counted_as_an_attempt(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805", recoveryAfterMinutes="10"))
    devices.add(_plug(make_device))
    _down_for(hub, 20, now)
    device_cmds.raises = RuntimeError("plug unreachable")
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)
    assert hub.states.get("recoveryAttempts", 0) == 0
    assert any("Could not power-cycle" in line for line in plugin.logger.lines["error"])


# ------------------------------------------------------------- coming back

def test_coming_back_clears_the_latch_and_reports_how_long_it_was_away(plugin, devices, make_device):
    now = datetime.now()
    hub = devices.add(_hub(make_device))
    _down_for(hub, 162, now)
    hub.states["recoveryAttempts"] = 2
    hub.errorState = "unreachable"
    plugin._hub_answers = lambda dev: True

    plugin._check_hub(hub)

    assert hub.states["connectionState"] == "Connected"
    assert hub.states["unreachableSince"] == ""
    assert hub.states["recoveryAttempts"] == 0
    assert hub.errorState == ""
    recovered = [line for line in plugin.logger.lines["info"] if "answering again" in line]
    assert len(recovered) == 1
    assert "2 hours and 42 minutes" in recovered[0]


def test_a_healthy_hub_says_nothing_at_all(plugin, devices, make_device):
    hub = devices.add(_hub(make_device))
    plugin._hub_answers = lambda dev: True
    for _ in range(3):
        plugin._check_hub(hub)
    assert plugin.logger.lines["info"] == []
    assert plugin.logger.lines["error"] == []
    assert hub.states["connectionState"] == "Connected"
    assert hub.states["lastCheckedAt"]


# ------------------------------------------------------- config robustness

@pytest.mark.parametrize("bad", ["", "   ", "off", None, "ten"])
def test_rubbish_in_any_config_field_falls_back_instead_of_crashing(plugin, devices, make_device, device_cmds, bad):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug=bad, recoveryAfterMinutes=bad,
                           recoveryOffSeconds=bad, recoveryMaxAttempts=bad,
                           heartbeatMinutes=bad))
    devices.add(_plug(make_device))
    _down_for(hub, 600, now)
    plugin._hub_answers = lambda dev: False
    plugin._check_hub(hub)            # must not raise
    assert hub.states["connectionState"] == "Unreachable"


def test_an_absurd_off_duration_is_clamped(plugin, devices, make_device, device_cmds):
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805",
                           recoveryAfterMinutes="10", recoveryOffSeconds="99999"))
    devices.add(_plug(make_device))
    _down_for(hub, 20, now)
    plugin._hub_answers = lambda dev: False
    plugin._check_hub(hub)
    assert device_cmds.calls == [("off", 814381805, 60)]


def test_the_watchdog_is_off_when_the_interval_is_never(plugin, devices, make_device):
    devices.add(_hub(make_device, heartbeatMinutes="0"))
    probed = []
    plugin._hub_answers = lambda dev: probed.append(dev) or False
    plugin._watchdog_pass()
    assert probed == []


def test_a_learn_in_progress_suspends_the_watchdog(plugin, devices, make_device):
    devices.add(_hub(make_device))
    probed = []
    plugin._hub_answers = lambda dev: probed.append(dev) or False
    plugin._learn_lock.acquire()
    try:
        plugin._watchdog_pass()
    finally:
        plugin._learn_lock.release()
    assert probed == [], "probing mid-learn disturbs the capture and overwrites its state"


def test_a_disabled_hub_is_left_alone(plugin, devices, make_device):
    hub = _hub(make_device)
    hub.enabled = False
    devices.add(hub)
    probed = []
    plugin._hub_answers = lambda dev: probed.append(dev) or False
    plugin._watchdog_pass()
    assert probed == []


# ---------------------------------------------------------- the plug picker

def test_the_plug_picker_offers_none_and_excludes_our_own_one_way_relays(plugin, devices, make_device):
    devices.add(_plug(make_device))
    devices.add(make_device(614164061, "Fire On/Off", "rfRelay"))
    options = plugin.switchable_devices()
    assert options[0] == ("0", "None -- report only")
    ids = [oid for oid, _ in options]
    assert "814381805" in ids
    assert "614164061" not in ids, "an RF relay cannot cut its own hub's mains"


# ------------------------------------------------------------- probe policy

def test_one_missed_probe_is_not_evidence_of_absence(plugin, devices, make_device):
    hub = devices.add(_hub(make_device))
    calls = {"n": 0}

    def flaky(host, port=80, timeout=0):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("timed out")
        return object()

    plugin._broadlink.hello = flaky
    assert plugin._hub_answers(hub) is True
    assert calls["n"] == 2


def test_a_hub_with_no_address_is_never_called_reachable(plugin, devices, make_device):
    hub = devices.add(_hub(make_device, host=""))
    plugin._broadlink.hello = lambda *a, **k: object()
    assert plugin._hub_answers(hub) is False


# ---------------------------------------------------- gaps the sweep found
#
# Both of these were written because a mutation SURVIVED the first sweep: the
# behaviour was correct but nothing pinned it, because another guard happened to
# mask it. A guard that is only ever reached behind a second guard is untested.

def test_the_give_up_holds_even_once_the_grace_period_has_passed(plugin, devices, make_device, device_cmds):
    # The first version of the "stops after the last attempt" test kept
    # lastRecoveryAt recent, so the inter-attempt grace was doing the work and
    # the max-attempts guard could be deleted without a single test failing.
    now = datetime.now()
    hub = devices.add(_hub(make_device, recoveryPlug="814381805",
                           recoveryAfterMinutes="10", recoveryMaxAttempts="2"))
    devices.add(_plug(make_device))
    _down_for(hub, 300, now)
    hub.states["recoveryAttempts"] = 2
    hub.states["lastRecoveryAt"] = (now - timedelta(minutes=240)).strftime(STAMP)
    plugin._hub_answers = lambda dev: False

    for _ in range(3):
        plugin._check_hub(hub)

    assert device_cmds.calls == [], "attempts are spent; a long wait must not revive them"
    assert hub.states["recoveryAttempts"] == 2
    assert [line for line in plugin.logger.lines["error"] if "Leaving it alone" in line] == []


def test_the_first_miss_never_cuts_power_even_with_a_zero_threshold(plugin, devices, make_device, device_cmds):
    # The early return on the first miss is defence in depth: normally the
    # elapsed time is zero so the threshold blocks it anyway, which meant the
    # return could be deleted unnoticed. Force the threshold to zero and the
    # return is the only thing standing between a single dropped packet and the
    # hub losing its mains.
    hub = devices.add(_hub(make_device, recoveryPlug="814381805", recoveryAfterMinutes="0"))
    devices.add(_plug(make_device))
    plugin._hub_answers = lambda dev: False

    plugin._check_hub(hub)

    assert device_cmds.calls == [], "one missed probe must never reach for the power"
    assert hub.states["unreachableSince"]
