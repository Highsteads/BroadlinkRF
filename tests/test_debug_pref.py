#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_debug_pref.py
# Description: The Configure dialog's Debug box takes effect on Save (1.6.1).
#              It was read only at startup, so unticking it left debug lines
#              in the event log until the plugin restarted.
# Author:      CliveS & Claude Opus 5.5
# Date:        04-10-2026
# Version:     1.0


def test_unticking_debug_turns_it_off_at_once(plugin):
    plugin.debug = True
    plugin.closedPrefsConfigUi({"debugLogging": False}, False)
    assert plugin.debug is False


def test_ticking_debug_turns_it_on_at_once(plugin):
    plugin.debug = False
    plugin.closedPrefsConfigUi({"debugLogging": True}, False)
    assert plugin.debug is True


def test_cancel_changes_nothing(plugin):
    plugin.debug = True
    plugin.closedPrefsConfigUi({"debugLogging": False}, True)
    assert plugin.debug is True
