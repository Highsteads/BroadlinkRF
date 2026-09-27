#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_learn_and_reload.py
# Description: Three faults found while writing the guide: a blank default
#              frequency the Configure dialog refused (and would have read as
#              433.92), Reload RF Code Store on a command device reloading the
#              wrong store, and Learn RF Command leaving a Command device's
#              Selected RF Code state naming a code it does not send.
# Author:      CliveS & Claude Opus 5.5
# Date:        27-09-2026
# Version:     1.0

import json
import types


def _prefs(**overrides):
    values = {
        "defaultHost": "192.168.1.100",
        "defaultPort": "80",
        "defaultFrequency": "433.92",
        "defaultRepeat": "3",
        "codeStorePath": "/tmp/broadlink_codes.json",
    }
    values.update(overrides)
    return values


def _store(path, names):
    path.write_text(json.dumps({
        name: {"frequency": 433.92, "packet": "aa" * 24} for name in names
    }), encoding="utf-8")
    return str(path)


# -- Default RF frequency: blank is accepted, and means scan -----------------

def test_configure_accepts_a_blank_default_frequency(plugin):
    result = plugin.validatePrefsConfigUi(_prefs(defaultFrequency=""))
    assert result[0] is True


def test_configure_still_refuses_a_nonsense_frequency(plugin):
    ok, _values, errors = plugin.validatePrefsConfigUi(_prefs(defaultFrequency="abc"))
    assert ok is False
    assert "defaultFrequency" in errors


def test_a_blank_default_frequency_means_scan_like_zero(plugin, make_device):
    hub = make_device(1, "Hub")          # no frequency of its own
    plugin.pluginPrefs["defaultFrequency"] = ""
    assert plugin._hub_frequency(hub) == 0.0
    plugin.pluginPrefs["defaultFrequency"] = "0"
    assert plugin._hub_frequency(hub) == 0.0


def test_an_unset_default_frequency_is_still_433_92(plugin, make_device):
    hub = make_device(1, "Hub")
    plugin.pluginPrefs.pop("defaultFrequency", None)
    assert plugin._hub_frequency(hub) == 433.92


def test_the_hubs_own_frequency_still_wins(plugin, make_device):
    hub = make_device(1, "Hub", props={"frequency": "315"})
    plugin.pluginPrefs["defaultFrequency"] = ""
    assert plugin._hub_frequency(hub) == 315.0


# -- Reload RF Code Store on a Command or Relay device -----------------------

def test_reload_on_a_command_device_reloads_its_hubs_store(plugin, devices, make_device,
                                                          tmp_path):
    plugin.pluginPrefs["codeStorePath"] = _store(tmp_path / "plugin.json", ["one"])
    hub = devices.add(make_device(1, "Hub", props={
        "codeStorePath": _store(tmp_path / "hub.json", ["fire_on", "fire_off"])}))
    for type_id in ("rfCommand", "rfRelay"):
        dev = devices.add(make_device(900, "Fire", device_type_id=type_id,
                                      props={"hubDevice": str(hub.id)}))
        seen = []
        real = plugin._load_codes
        plugin._load_codes = lambda hub=None, force=False, path=None: (
            seen.append((hub, force)) or real(hub, force, path))
        plugin.import_codes(types.SimpleNamespace(props={}), dev)
        plugin._load_codes = real
        assert seen == [(hub, True)]
        assert "RF code store for 'Hub' reloaded: 2 code(s) available" in plugin.logger.lines["info"]


def test_reload_with_no_hub_says_so_and_reloads_nothing(plugin, devices, make_device):
    devices.add(make_device(1, "Hub A"))
    devices.add(make_device(2, "Hub B"))       # two hubs: no fallback
    dev = devices.add(make_device(900, "Fire", device_type_id="rfCommand"))
    called = []
    plugin._load_codes = lambda *a, **k: called.append(a) or {}
    plugin.import_codes(types.SimpleNamespace(props={}), dev)
    assert called == []
    assert any("No RM4 Pro selected for 'Fire'" in line for line in plugin.logger.lines["error"])


# -- Learn RF Command on a Command device ------------------------------------

class _FakeRM4:
    def find_rf_packet(self, frequency):
        pass

    def check_data(self):
        return b"\x26" * 32


def _learn(plugin, hub, target, name, frequency=433.92):
    plugin.sleep = lambda seconds: None
    plugin._connect = lambda hub: _FakeRM4()
    plugin._learn_worker(hub, name, frequency, target)


def test_learning_another_name_leaves_the_commands_selection_alone(plugin, devices,
                                                                  make_device, tmp_path):
    """The action saves a code under a name. The device still sends the code in
    its settings, so its Selected RF Code state must go on naming that one."""
    hub = devices.add(make_device(1, "Hub", props={
        "codeStorePath": _store(tmp_path / "hub.json", ["fire_on"])}))
    cmd = devices.add(make_device(900, "Fire On", device_type_id="rfCommand",
                                  props={"hubDevice": "1", "codeName": "fire_on"},
                                  states={"selectedCode": "fire_on", "selectedFrequency": 433.92}))
    _learn(plugin, hub, cmd, "new_code", frequency=315.0)
    assert "new_code" in json.loads((tmp_path / "hub.json").read_text())
    assert cmd.pluginProps["codeName"] == "fire_on"
    assert cmd.states["selectedCode"] == "fire_on"
    assert cmd.states["selectedFrequency"] == 433.92
    assert cmd.states["lastResult"] == "Learned"


def test_relearning_the_commands_own_code_updates_its_frequency(plugin, devices,
                                                               make_device, tmp_path):
    hub = devices.add(make_device(1, "Hub", props={
        "codeStorePath": _store(tmp_path / "hub.json", ["fire_on"])}))
    cmd = devices.add(make_device(900, "Fire On", device_type_id="rfCommand",
                                  props={"hubDevice": "1", "codeName": "fire_on"},
                                  states={"selectedCode": "fire_on", "selectedFrequency": 433.92}))
    _learn(plugin, hub, cmd, "fire_on", frequency=315.0)
    assert cmd.states["selectedCode"] == "fire_on"
    assert cmd.states["selectedFrequency"] == 315.0


def test_learning_on_a_relay_writes_no_selection_states(plugin, devices, make_device,
                                                        tmp_path):
    """A relay declares no selectedCode or selectedFrequency state, so writing
    them would be refused by Indigo."""
    hub = devices.add(make_device(1, "Hub", props={
        "codeStorePath": _store(tmp_path / "hub.json", [])}))
    relay = devices.add(make_device(900, "Fire", device_type_id="rfRelay",
                                    props={"hubDevice": "1"}))
    _learn(plugin, hub, relay, "fire_on")
    assert "selectedCode" not in relay.states
    assert relay.states["lastResult"] == "Learned"


def test_learn_action_on_a_hub_uses_that_hub(plugin, devices, make_device):
    """_hub_for_command() reads a hubDevice prop a hub does not have, so with two
    hubs a learn run on a hub found none at all."""
    hub_a = devices.add(make_device(1, "Hub A"))
    devices.add(make_device(2, "Hub B"))
    started = []
    plugin._start_learning = lambda hub, name, freq, target_dev=None: started.append(
        (hub, name, target_dev))
    plugin.learn_rf_command(types.SimpleNamespace(props={"codeName": "x", "frequency": "0"}), hub_a)
    assert started == [(hub_a, "x", None)]
