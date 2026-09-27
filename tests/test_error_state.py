#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_error_state.py
# Description: The watchdog's "unreachable" error on a hub must survive the
#              plugin's own routine state writes, and clear only when the plugin
#              decides the outage is over. Also: a Command device is never
#              written a state it does not declare.
# Author:      CliveS & Claude Opus 5.5
# Date:        27-09-2026
# Version:     1.0

import ast
import pathlib
import types
from datetime import datetime, timedelta

import pytest

STAMP = "%Y-%m-%d %H:%M:%S"
REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_PY = next(REPO.glob("*.indigoPlugin/Contents/Server Plugin/plugin.py"))
DEVICES_XML = PLUGIN_PY.with_name("Devices.xml")


@pytest.fixture(params=[True, False], ids=["batch-takes-flag", "batch-refuses-flag"])
def quiet_hub(request, plugin, devices, make_device):
    """A hub already latched as unreachable, with its error showing."""
    hub = make_device(20637040, "Broadlink RM4 Pro", "rm4Pro",
                      props={"host": "192.168.1.200", "port": "80", "heartbeatMinutes": "5"})
    hub.batch_takes_clear_flag = request.param
    devices.add(hub)
    plugin._hub_answers = lambda dev: False
    plugin._check_hub(hub)
    assert hub.errorState == "unreachable"
    return hub


def test_the_error_survives_the_next_watchdog_pass(plugin, quiet_hub):
    # Before 1.6.0 this write of connectionState/lastCheckedAt wiped the error
    # on the very next pass, five minutes later.
    plugin._check_hub(quiet_hub)
    plugin._check_hub(quiet_hub)
    assert quiet_hub.errorState == "unreachable"
    assert quiet_hub.states["connectionState"] == "Unreachable"


def test_the_error_survives_a_failed_send(plugin, quiet_hub):
    plugin._load_codes = lambda hub=None, **kw: {"fire_on": {"packet": "00ff", "frequency": 433.92}}

    def broken_connect(hub):
        raise OSError("timed out")
    plugin._connect = broken_connect

    assert plugin._send_code(quiet_hub, "fire_on") is False
    assert quiet_hub.states["lastResult"] == "Failed"
    assert quiet_hub.errorState == "unreachable"


def test_the_error_survives_a_power_cycle_attempt(plugin, quiet_hub, devices, make_device, device_cmds):
    devices.add(make_device(814381805, "Fire Plug", "shellyRelay",
                            plugin_id="com.clives.indigoplugin.shellydirect"))
    quiet_hub.pluginProps.update(recoveryPlug="814381805", recoveryAfterMinutes="10")
    quiet_hub.states["unreachableSince"] = (datetime.now() - timedelta(minutes=12)).strftime(STAMP)
    plugin._check_hub(quiet_hub)
    assert device_cmds.calls, "the cycle should have happened"
    assert quiet_hub.states["recoveryAttempts"] == 1
    assert quiet_hub.errorState == "unreachable"


def test_the_error_clears_when_the_hub_answers_again(plugin, quiet_hub):
    plugin._hub_answers = lambda dev: True
    plugin._check_hub(quiet_hub)
    assert quiet_hub.errorState == ""
    assert quiet_hub.states["unreachableSince"] == ""


def test_a_stray_error_on_a_healthy_hub_is_cleared_when_it_answers(plugin, devices, make_device):
    hub = devices.add(make_device(20637040, "Broadlink RM4 Pro", "rm4Pro",
                                  props={"host": "192.168.1.200", "heartbeatMinutes": "5"}))
    hub.errorState = "unreachable"          # left from before an upgrade, say
    plugin._hub_answers = lambda dev: True
    plugin._check_hub(hub)
    assert hub.errorState == ""


def test_turning_the_watchdog_off_lets_go_of_the_outage(plugin, quiet_hub):
    quiet_hub.pluginProps["heartbeatMinutes"] = "0"
    plugin._watchdog_pass()
    assert quiet_hub.errorState == ""
    assert quiet_hub.states["unreachableSince"] == ""
    assert quiet_hub.states["connectionState"] == "Configured"
    said = [line for line in plugin.logger.lines["info"] if "no longer checked" in line]
    assert len(said) == 1
    plugin._watchdog_pass()
    assert len([line for line in plugin.logger.lines["info"] if "no longer checked" in line]) == 1


def test_the_watchdog_off_leaves_a_healthy_hub_alone(plugin, devices, make_device):
    hub = devices.add(make_device(20637040, "Broadlink RM4 Pro", "rm4Pro",
                                  props={"heartbeatMinutes": "0"}))
    plugin._watchdog_pass()
    assert hub.state_writes == []
    assert plugin.logger.lines["info"] == []


def test_a_refused_batch_flag_is_remembered_and_writes_go_one_at_a_time(plugin, devices, make_device):
    hub = devices.add(make_device(20637040, "Broadlink RM4 Pro", "rm4Pro",
                                  props={"host": "192.168.1.200", "heartbeatMinutes": "5"}))
    hub.batch_takes_clear_flag = False
    hub.errorState = "unreachable"
    plugin._update_states(hub, lastResult="a")
    assert plugin._batch_keeps_error is False
    assert hub.state_writes == [], "the refused batch must not have written anything"
    before = hub.single_writes
    plugin._update_states(hub, lastResult="x", lastError="y")
    assert hub.single_writes == before + 2
    assert hub.errorState == "unreachable"


def test_every_batch_state_write_goes_through_the_helper():
    """A new direct batch write would quietly start wiping the error again."""
    tree = ast.parse(PLUGIN_PY.read_text(encoding="utf-8"))
    offenders = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef) or fn.name == "_update_states":
            continue
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "updateStatesOnServer"):
                offenders.append(fn.name)
    assert offenders == []


# ------------------------------------------------ lastCommand on a Command device

def _declared_states(device_type):
    import xml.etree.ElementTree as ET
    root = ET.parse(DEVICES_XML).getroot()
    for dev in root.findall("Device"):
        if dev.get("id") == device_type:
            return {s.get("id") for s in dev.find("States")}
    raise AssertionError(device_type)


@pytest.mark.parametrize("device_type", ["rfCommand", "rfRelay"])
def test_a_send_writes_only_states_the_device_declares(plugin, devices, make_device, device_type):
    hub = devices.add(make_device(20637040, "Broadlink RM4 Pro", "rm4Pro",
                                  props={"host": "192.168.1.200"}))
    target = devices.add(make_device(1621408282, "Fire On", device_type,
                                     props={"hubDevice": str(hub.id), "codeName": "fire_on"}))
    plugin._load_codes = lambda hub=None, **kw: {"fire_on": {"packet": "00ff", "frequency": 433.92}}
    plugin._connect = lambda hub: types.SimpleNamespace(send_data=lambda packet: None)

    assert plugin._send_code(hub, "fire_on", repeat=1, target_dev=target) is True

    written = set().union(*target.state_writes)
    assert written <= _declared_states(device_type), written - _declared_states(device_type)
    assert target.states["lastResult"] == "Sent"
    if device_type == "rfRelay":
        assert target.states["lastCommand"] == "fire_on"
    for w in hub.state_writes:
        assert set(w) <= _declared_states("rm4Pro")
