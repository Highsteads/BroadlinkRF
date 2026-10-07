#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_dialog_xml.py
# Description: Fail when a dialog field is bound with a value that starts "!".
#              Indigo has no negation: a bound field is visible (or enabled) when the
#              binding VALUE STRING CONTAINS the bound field's current value, so "!0"
#              shows a field only while the bound menu is "0" -- the reverse of the
#              intent. Reads the XML; imports nothing. Generic: finds the bundle by
#              glob, so it drops into any plugin repo unchanged.
# Author:      CliveS & Claude Opus 5.5
# Date:        07-10-2026
# Version:     1.0

import glob
import os
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_FILES = sorted(glob.glob(os.path.join(REPO, "*.indigoPlugin", "Contents", "Server Plugin", "*.xml")))

# Indigo's binding attributes that take a value to compare with the bound field.
BINDING_VALUE_ATTRS = ("visibleBindingValue", "enabledBindingValue")


def negated_bindings(xml_text):
    """Return (field id, attribute, value) for every binding value that starts with '!'."""
    found = []
    for element in ET.fromstring(xml_text).iter():
        for attr in BINDING_VALUE_ATTRS:
            value = element.get(attr)
            if value is not None and value.strip().startswith("!"):
                found.append((element.get("id", element.tag), attr, value))
    return found


def test_the_bundle_has_xml_to_check():
    assert XML_FILES, "no dialog XML found under *.indigoPlugin/Contents/Server Plugin"


def test_no_binding_value_starts_with_a_bang():
    # "!0" is not "anything but 0" in Indigo: it shows the field only while the value is "0".
    bad = []
    for path in XML_FILES:
        with open(path, encoding="utf-8") as fh:
            for field_id, attr, value in negated_bindings(fh.read()):
                bad.append(f"{os.path.basename(path)}: field '{field_id}' {attr}=\"{value}\"")
    assert not bad, "Indigo has no negation in a binding value:\n" + "\n".join(bad)


def test_the_check_can_fail():
    # A guard is only a guard once it has been seen to fail.
    sample = (
        '<Root><Field id="a" visibleBindingId="b" visibleBindingValue="!0"/>'
        '<Field id="c" enabledBindingId="b" enabledBindingValue="!none"/>'
        '<Field id="d" visibleBindingId="b" visibleBindingValue="1,2"/></Root>'
    )
    assert negated_bindings(sample) == [
        ("a", "visibleBindingValue", "!0"),
        ("c", "enabledBindingValue", "!none"),
    ]
