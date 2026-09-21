#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    conftest.py
# Description: Loads plugin.py outside Indigo behind a stub `indigo` module, so the
#              watchdog's decisions can be tested with no hub, no network and no
#              Indigo server.
# Author:      CliveS & Claude Opus 5
# Date:        19-09-2026
# Version:     1.0

import importlib.util
import pathlib
import sys
import types

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_PY = next(REPO.glob("*.indigoPlugin/Contents/Server Plugin/plugin.py"))


class StopThread(Exception):
    """Stands in for indigo's own StopThread."""


class FakeDevice:
    def __init__(self, dev_id, name, device_type_id="rm4Pro", props=None,
                 states=None, enabled=True, plugin_id="com.clives.indigoplugin.broadlinkrf"):
        self.id = dev_id
        self.name = name
        self.deviceTypeId = device_type_id
        self.pluginProps = dict(props or {})
        self.states = dict(states or {})
        self.enabled = enabled
        self.pluginId = plugin_id
        self.errorState = ""
        self.lastSuccessfulComm = None
        self.state_writes = []

    @property
    def onState(self):
        return bool(self.states.get("onOffState", False))

    def stateListOrDisplayStateIdChanged(self):
        pass

    def updateStatesOnServer(self, rows):
        for row in rows:
            self.states[row["key"]] = row["value"]
        self.state_writes.append({r["key"]: r["value"] for r in rows})

    def updateStateOnServer(self, key, value):
        self.states[key] = value

    def setErrorStateOnServer(self, message):
        self.errorState = message


class FakeDevices:
    """Mimics indigo.devices: subscriptable by id, iterable by filter."""

    def __init__(self):
        self._by_id = {}
        self.subscribed = 0

    def subscribeToChanges(self):
        self.subscribed += 1

    def add(self, dev):
        self._by_id[dev.id] = dev
        return dev

    def __getitem__(self, dev_id):
        try:
            return self._by_id[int(dev_id)]
        except (TypeError, ValueError):
            raise KeyError(dev_id)
        except KeyError:
            raise

    def iter(self, filt=""):
        for dev in list(self._by_id.values()):
            if filt == "self":
                if dev.pluginId == "com.clives.indigoplugin.broadlinkrf":
                    yield dev
            elif filt == "indigo.relay":
                if dev.deviceTypeId in ("rfRelay", "relay", "shellyRelay"):
                    yield dev
            else:
                yield dev


class FakeDeviceCmds:
    def __init__(self):
        self.calls = []
        self.raises = None

    def turnOff(self, dev_id, delay=0, duration=0, **kw):
        if self.raises:
            raise self.raises
        self.calls.append(("off", int(dev_id), duration))

    def turnOn(self, dev_id, delay=0, duration=0, **kw):
        self.calls.append(("on", int(dev_id), duration))


class RecordingLogger:
    def __init__(self):
        self.lines = {"debug": [], "info": [], "warning": [], "error": [], "exception": []}

    def _rec(self, level, msg, *args):
        try:
            self.lines[level].append(msg % args if args else str(msg))
        except Exception:
            self.lines[level].append(str(msg))

    def debug(self, m, *a):     self._rec("debug", m, *a)
    def info(self, m, *a):      self._rec("info", m, *a)
    def warning(self, m, *a):   self._rec("warning", m, *a)
    def error(self, m, *a):     self._rec("error", m, *a)
    def exception(self, m, *a): self._rec("exception", m, *a)


def _make_indigo_stub():
    mod = types.ModuleType("indigo")

    class PluginBase:
        StopThread = StopThread

        def __init__(self, plugin_id, display_name, version, prefs, **kw):
            self.pluginId = plugin_id
            self.pluginDisplayName = display_name
            self.pluginVersion = version
            self.pluginPrefs = dict(prefs or {})
            self.logger = RecordingLogger()
            self.slept = []

        def sleep(self, seconds):
            self.slept.append(seconds)
            raise StopThread()

        def deviceUpdated(self, orig, new):
            pass

    mod.PluginBase = PluginBase
    mod.devices = FakeDevices()
    mod.device = FakeDeviceCmds()
    mod.Dict = dict
    mod.List = list
    mod.kDeviceAction = types.SimpleNamespace(TurnOn=1, TurnOff=2, Toggle=3)
    mod.kUniversalAction = types.SimpleNamespace(RequestStatus=10)
    mod.server = types.SimpleNamespace(
        getInstallFolderPath=lambda: "/tmp",
        log=lambda *a, **k: None,
    )
    return mod


@pytest.fixture
def plugin_module():
    stub = _make_indigo_stub()
    sys.modules["indigo"] = stub
    spec = importlib.util.spec_from_file_location("broadlinkrf_plugin_under_test", PLUGIN_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module._stub_indigo = stub
    yield module
    sys.modules.pop(spec.name, None)
    sys.modules.pop("indigo", None)


@pytest.fixture
def plugin(plugin_module):
    p = plugin_module.Plugin("com.clives.indigoplugin.broadlinkrf", "Broadlink RF", "1.3.0", {})
    p._broadlink = types.SimpleNamespace(hello=lambda *a, **k: object())
    p.indigo = plugin_module._stub_indigo
    return p


@pytest.fixture
def devices(plugin_module):
    return plugin_module._stub_indigo.devices


@pytest.fixture
def device_cmds(plugin_module):
    return plugin_module._stub_indigo.device


@pytest.fixture
def make_device(plugin_module):
    return FakeDevice
