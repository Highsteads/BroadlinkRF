#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_feedback.py
# Description: Power-meter feedback on the RF relay (v1.4.0). The relay's state
#              follows a meter's watts, a sent command waits for the meter to
#              agree, and a missing reading falls back to open loop and says so.
# Author:      CliveS & Claude Opus 5
# Date:        21-09-2026
# Version:     1.0

from datetime import datetime, timedelta

import pytest


PLUG_ID = 50
RELAY_ID = 60


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock(plugin):
    c = Clock()
    plugin._monotonic = c
    return c


@pytest.fixture
def plug(devices, make_device):
    return devices.add(make_device(PLUG_ID, "Living Room Fire Plug", device_type_id="shellyRelay",
                                   states={"powerWatts": 0.5, "onOffState": True},
                                   plugin_id="com.clives.indigoplugin.shellydirect"))


def _relay(devices, make_device, **props):
    base = {"hubDevice": "1", "onCodeName": "fire_on", "offCodeName": "fire_off",
            "feedbackDevice": str(PLUG_ID), "feedbackStateName": "powerWatts",
            "feedbackOnWatts": "10", "feedbackTimeoutSeconds": "90", "feedbackHeavyWatts": "500"}
    base.update(props)
    return devices.add(make_device(RELAY_ID, "Fire On/Off", device_type_id="rfRelay", props=base,
                                   states={"onOffState": False}))


@pytest.fixture
def relay(plugin, devices, make_device, plug, clock):
    r = _relay(devices, make_device)
    plugin._send_from_device = lambda dev, code: True
    plugin.deviceStartComm(r)
    return r


def _action(plugin_module, name):
    import types
    ka = plugin_module._stub_indigo.kDeviceAction
    return types.SimpleNamespace(deviceAction=getattr(ka, name))


def _report(plugin, plug, watts):
    plug.states["powerWatts"] = watts
    plugin.deviceUpdated(plug, plug)


# -- following the reading --------------------------------------------------

def test_startup_reads_the_meter(relay):
    assert relay.states["measuredState"] == "off"
    assert relay.states["feedbackStatus"] == "Off (measured)"
    assert relay.states["measuredWatts"] == 0.5


def test_startup_subscribes_only_when_a_meter_is_configured(plugin, devices, make_device):
    r = devices.add(make_device(61, "Blind", device_type_id="rfRelay", props={"hubDevice": "1"}))
    plugin.deviceStartComm(r)
    assert devices.subscribed == 0
    assert r.states["measuredState"] == "unknown"
    assert r.states["feedbackStatus"] == "Not configured"


def test_a_handset_press_turns_the_relay_on_and_says_so(plugin, relay, plug):
    _report(plugin, plug, 37.1)
    assert relay.states["onOffState"] is True
    assert relay.states["measuredState"] == "on"
    assert any("something other than this plugin" in line for line in plugin.logger.lines["info"])


def test_a_changing_reading_does_not_rewrite_unchanged_states(plugin, relay, plug):
    _report(plugin, plug, 37.1)
    writes = len(relay.state_writes)
    _report(plugin, plug, 37.1)
    assert len(relay.state_writes) == writes


def test_own_plugin_updates_are_ignored(plugin, relay, plug):
    """The loop guard: a change to one of OUR devices never re-enters the
    handler, even when that device's id is one we are watching."""
    called = []
    plugin._apply_reading = lambda *a, **k: called.append(1)
    plug.pluginId = plugin.pluginId
    plugin.deviceUpdated(plug, plug)
    assert called == []


def test_the_threshold_is_the_on_line(plugin, relay, plug):
    _report(plugin, plug, 9.9)
    assert relay.states["onOffState"] is False
    _report(plugin, plug, 10.0)
    assert relay.states["onOffState"] is True


def test_heavy_load_follows_its_own_line(plugin, relay, plug):
    _report(plugin, plug, 38)
    assert relay.states["heavyLoad"] is False
    _report(plugin, plug, 1510)
    assert relay.states["heavyLoad"] is True
    assert any("heavy-load line" in line for line in plugin.logger.lines["info"])
    _report(plugin, plug, 38)
    assert relay.states["heavyLoad"] is False


def test_heavy_load_off_when_no_line_is_set(plugin, devices, make_device, plug, clock):
    r = _relay(devices, make_device, feedbackHeavyWatts="")
    plugin.deviceStartComm(r)
    _report(plugin, plug, 1510)
    assert r.states["heavyLoad"] is False


# -- confirming a sent command -------------------------------------------------

def test_a_send_waits_then_confirms(plugin, plugin_module, relay, plug, clock):
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    assert relay.states["onOffState"] is True          # optimistic, as before
    assert relay.states["feedbackStatus"] == "Waiting for on"
    clock.now += 29
    _report(plugin, plug, 38.0)
    assert relay.states["feedbackStatus"] == "On (measured)"
    assert plugin._pending == {}
    assert plugin.logger.lines["warning"] == []


def test_a_stale_reading_during_the_wait_does_not_flip_it_back(plugin, plugin_module, relay,
                                                               plug, clock):
    """The meter reports on its own schedule; the first reading after a send
    often predates the appliance acting on it."""
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    clock.now += 5
    _report(plugin, plug, 0.5)
    assert relay.states["onOffState"] is True
    assert relay.states["feedbackStatus"] == "Waiting for on"


def test_no_response_times_out_to_the_reading_with_a_warning(plugin, plugin_module, relay,
                                                             plug, clock):
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    clock.now += 91
    plugin._feedback_pass()
    assert relay.states["onOffState"] is False
    assert relay.states["feedbackStatus"] == "Did not turn on"
    assert len(plugin.logger.lines["warning"]) == 1
    assert "has not responded" in plugin.logger.lines["warning"][0]
    plugin._feedback_pass()                               # said once, not every pass
    assert len(plugin.logger.lines["warning"]) == 1


def test_the_failure_stays_visible_until_the_reading_changes(plugin, plugin_module, relay,
                                                             plug, clock):
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    clock.now += 91
    plugin._feedback_pass()
    _report(plugin, plug, 0.6)
    assert relay.states["feedbackStatus"] == "Did not turn on"
    _report(plugin, plug, 37)
    assert relay.states["feedbackStatus"] == "On (measured)"


def test_off_is_confirmed_the_same_way(plugin, plugin_module, relay, plug, clock):
    _report(plugin, plug, 37)
    plugin.actionControlDevice(_action(plugin_module, "TurnOff"), relay)
    assert relay.states["feedbackStatus"] == "Waiting for off"
    _report(plugin, plug, 0.5)
    assert relay.states["onOffState"] is False
    assert relay.states["feedbackStatus"] == "Off (measured)"


def test_toggle_flips_from_the_reading_not_the_last_send(plugin, plugin_module, relay, plug):
    """Lit from the handset: the reading says on, so a toggle must send OFF."""
    sent = []
    plugin._send_from_device = lambda dev, code: sent.append(code) or True
    _report(plugin, plug, 37)
    plugin.actionControlDevice(_action(plugin_module, "Toggle"), relay)
    assert sent == ["fire_off"]
    assert relay.states["feedbackStatus"] == "Waiting for off"   # and it waits for proof


def test_a_failed_send_waits_for_nothing(plugin, plugin_module, relay):
    plugin._send_from_device = lambda dev, code: False
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    assert plugin._pending == {}


# -- losing the reading ----------------------------------------------------------

@pytest.mark.parametrize("breakage, why", [
    (lambda plug, devices: setattr(plug, "enabled", False), "disabled"),
    (lambda plug, devices: setattr(plug, "errorState", "offline"), "in error"),
    (lambda plug, devices: plug.states.update(powerWatts=None), "no numeric"),
    (lambda plug, devices: setattr(plug, "lastSuccessfulComm",
                                   datetime.now() - timedelta(minutes=40)), "not reported"),
    (lambda plug, devices: devices._by_id.pop(PLUG_ID), "no longer exists"),
])
def test_an_unusable_meter_is_unknown_and_warned_once(plugin, relay, plug, devices, breakage, why):
    breakage(plug, devices)
    plugin._feedback_pass()
    plugin._feedback_pass()
    assert relay.states["measuredState"] == "unknown"
    assert relay.states["feedbackStatus"] == "No reading"
    assert len(plugin.logger.lines["warning"]) == 1
    assert why in plugin.logger.lines["warning"][0]


def test_a_fresh_meter_is_not_stale(plugin, relay, plug):
    plug.lastSuccessfulComm = datetime.now() - timedelta(minutes=2)
    plugin._feedback_pass()
    assert relay.states["measuredState"] == "off"


def test_the_warning_latch_survives_a_restart(plugin, relay, plug):
    plug.enabled = False
    plugin._feedback_pass()
    plugin.deviceStartComm(relay)                         # as after a plugin restart
    plugin._feedback_pass()
    assert len(plugin.logger.lines["warning"]) == 1


def test_recovery_is_announced(plugin, relay, plug):
    plug.enabled = False
    plugin._feedback_pass()
    plug.enabled = True
    plugin._feedback_pass()
    assert relay.states["measuredState"] == "off"
    assert any("again" in line for line in plugin.logger.lines["info"])


def test_with_no_reading_the_optimistic_state_stands(plugin, plugin_module, relay, plug, clock):
    plug.enabled = False
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    clock.now += 200
    plugin._feedback_pass()
    assert relay.states["onOffState"] is True
    assert plugin._pending == {}


def test_a_string_reading_is_accepted(plugin, relay, plug):
    _report(plugin, plug, "37.5")
    assert relay.states["measuredState"] == "on"


# -- configuration -------------------------------------------------------------

def test_stop_comm_forgets_the_relay(plugin, plugin_module, relay, plug):
    plugin.actionControlDevice(_action(plugin_module, "TurnOn"), relay)
    plugin.deviceStopComm(relay)
    assert plugin._pending == {}
    assert all(RELAY_ID not in ids for ids in plugin._meter_map.values())


def test_repointing_the_meter_moves_the_mapping(plugin, relay, devices, make_device):
    devices.add(make_device(70, "Other plug", device_type_id="shellyRelay",
                            states={"powerWatts": 3.0}, plugin_id="x"))
    relay.pluginProps["feedbackDevice"] = "70"
    plugin.deviceStartComm(relay)
    assert RELAY_ID not in plugin._meter_map.get(PLUG_ID, set())
    assert RELAY_ID in plugin._meter_map[70]


def _values(**over):
    v = {"feedbackDevice": str(PLUG_ID), "feedbackStateName": "", "feedbackOnWatts": "10",
         "feedbackTimeoutSeconds": "90", "feedbackHeavyWatts": ""}
    v.update(over)
    return v


def test_validation_picks_the_power_reading_when_left_blank(plugin, plug):
    values, errors = _values(), {}
    plugin._validate_feedback(values, errors)
    assert errors == {}
    assert values["feedbackStateName"] == "powerWatts"


@pytest.mark.parametrize("over, field", [
    ({"feedbackDevice": "999"}, "feedbackDevice"),
    ({"feedbackStateName": "onOffState"}, "feedbackStateName"),
    ({"feedbackOnWatts": "0"}, "feedbackOnWatts"),
    ({"feedbackOnWatts": "lots"}, "feedbackOnWatts"),
    ({"feedbackTimeoutSeconds": "5"}, "feedbackTimeoutSeconds"),
    ({"feedbackHeavyWatts": "5"}, "feedbackHeavyWatts"),
])
def test_validation_refuses_bad_settings(plugin, plug, over, field):
    errors = {}
    plugin._validate_feedback(_values(**over), errors)
    assert field in errors


def test_no_meter_needs_no_validation(plugin):
    errors = {}
    plugin._validate_feedback({"feedbackDevice": "0", "feedbackOnWatts": "junk"}, errors)
    assert errors == {}


def test_blank_config_is_safe(plugin, devices, make_device):
    """A relay saved before 1.4.0 carries none of these props."""
    r = devices.add(make_device(62, "Old relay", device_type_id="rfRelay", props={}))
    assert plugin._feedback_config(r) is None
    r.pluginProps.update(feedbackDevice=str(PLUG_ID), feedbackOnWatts="", feedbackTimeoutSeconds="")
    cfg = plugin._feedback_config(r)
    assert cfg["on_watts"] == 10.0 and cfg["timeout"] == 90 and cfg["heavy"] == 0.0


def test_meter_list_offers_only_devices_with_a_power_reading(plugin, plug, devices, make_device):
    devices.add(make_device(80, "Door contact", device_type_id="sensor",
                            states={"onOffState": False}, plugin_id="x"))
    ids = [i for i, _ in plugin.meter_devices()]
    assert str(PLUG_ID) in ids and "80" not in ids and ids[0] == "0"


def test_meter_states_lists_numbers_power_first(plugin, plug):
    plug.states.update(voltage=253.8, temperature=31)
    keys = [k for k, _ in plugin.meter_states(values_dict={"feedbackDevice": str(PLUG_ID)})]
    assert keys[0] == "powerWatts"
    assert "onOffState" not in keys


@pytest.mark.parametrize("watts, text", [(0.5, "0.5 W"), (37.1, "37 W"), (1512, "1,512 W"),
                                         (None, "no reading")])
def test_watts_read_as_a_person_says_them(plugin, watts, text):
    assert plugin._fmt_watts(watts) == text


def test_meter_states_with_no_meter_is_empty_not_a_blank_id(plugin):
    """Indigo rejects an option whose id is an empty string, and says so in red."""
    assert plugin.meter_states(values_dict={"feedbackDevice": "0"}) == []
