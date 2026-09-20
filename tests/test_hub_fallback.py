#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_hub_fallback.py
# Description: The "only one hub, so use it" fallback in _hub_for_command. It
#              counted every rm4Pro device rather than every USABLE one, while
#              the watchdog one page up already paired the type with `enabled`.
# Author:      CliveS & Claude Opus 5
# Date:        20-09-2026
# Version:     1.0


def _command(make_device, hub_prop=""):
    """An rfRelay whose configured hub is missing, so the fallback decides."""
    return make_device(900, "Fire On/Off", device_type_id="rfRelay",
                       props={"hubDevice": hub_prop})


def test_the_single_enabled_hub_is_used(plugin, devices, make_device):
    hub = make_device(1, "Broadlink RM4 Pro")
    devices.add(hub)
    cmd = _command(make_device)
    devices.add(cmd)
    assert plugin._hub_for_command(cmd) is hub


def test_a_lone_disabled_hub_is_refused_rather_than_returned(plugin, devices,
                                                             make_device):
    """Returning it sends the command into a hub that is out of service, and the
    failure then surfaces as a network timeout that names nothing."""
    devices.add(make_device(1, "Broadlink RM4 Pro", enabled=False))
    cmd = _command(make_device)
    devices.add(cmd)
    assert plugin._hub_for_command(cmd) is None


def test_a_disabled_spare_does_not_make_the_count_two(plugin, devices,
                                                      make_device):
    """The bug. One working hub and one shelf spare is a perfectly ordinary
    setup, and it made "exactly one hub" false — so every command with no
    explicit hub was refused while a usable hub sat there."""
    live = make_device(1, "Broadlink RM4 Pro")
    devices.add(live)
    devices.add(make_device(2, "Broadlink RM4 Pro (spare)", enabled=False))
    cmd = _command(make_device)
    devices.add(cmd)
    assert plugin._hub_for_command(cmd) is live


def test_two_enabled_hubs_are_still_ambiguous(plugin, devices, make_device):
    """With two usable hubs there is no right answer, so the fallback must not
    invent one — the device has to name its hub."""
    devices.add(make_device(1, "Hub A"))
    devices.add(make_device(2, "Hub B"))
    cmd = _command(make_device)
    devices.add(cmd)
    assert plugin._hub_for_command(cmd) is None


def test_an_explicitly_named_hub_wins_over_the_fallback(plugin, devices,
                                                        make_device):
    """The fallback only exists for a device that names no hub. A named one is
    used even where the fallback would have been ambiguous."""
    a = make_device(1, "Hub A")
    devices.add(a)
    devices.add(make_device(2, "Hub B"))
    cmd = _command(make_device, hub_prop="1")
    devices.add(cmd)
    assert plugin._hub_for_command(cmd) is a


def test_no_hubs_at_all_is_none(plugin, devices, make_device):
    cmd = _command(make_device)
    devices.add(cmd)
    assert plugin._hub_for_command(cmd) is None
