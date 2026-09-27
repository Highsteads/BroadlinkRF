---
title: Version history
nav_order: 10
---

# Version history

The newest version is at the top.

## 1.4.0 — 21 September 2026

- **A relay can follow a power meter** on the appliance it switches, such as the smart plug a fire runs from. Its On or Off then comes from the reading instead of the last button pressed.
- **Presses on the appliance's own remote show in Indigo,** and the log says the appliance was switched by something other than the plugin.
- **A press the appliance ignored is reported** as ignored, with the reading, instead of looking like a success.
- **Toggle goes the right way** even after someone used the handset.
- **New states** for triggers and control pages: **Measured Watts**, **Measured State**, **Feedback Status** and **Heavy Load**, the last set by an optional heavy-load line, such as 500 watts to show a fire's heater running.

## 1.3.2 — 20 September 2026

Notes in the code only, saying which lists deliberately include hubs that are disabled in Indigo. Nothing the plugin does changed.

## 1.3.1 — 20 September 2026

A device with no hub chosen now uses the one hub that is in service. Before, a spare hub disabled in Indigo counted as a second hub, so every such command was refused, and a single disabled hub was used anyway and failed with an error that did not say why.

## 1.3.0 — 19 September 2026

- **A watchdog on the hub.** The plugin checks the RM4 Pro on a timer, says once when it stops answering, shows it red in the device list, and says how long it was away when it returns. Before, a hub that had dropped off the network went unnoticed until a button press failed.
- **It can bring the hub back** by switching off the plug the hub runs from for a few seconds, with a limit on how many times it tries.
- New hub states: **Last Checked At**, **Unreachable Since**, **Recovery Attempts** and **Last Recovery At**.

## 1.2.2 — 11 September 2026

The plugin carries a note of where its code lives on GitHub, the same way other Indigo plugins do. Nothing else changed.

## 1.2.1 — 11 September 2026

Removed a line of code that did nothing. Nothing the plugin does changed.

## 1.2.0 — 28 August 2026

Indigo now installs the `broadlink` software the plugin needs by itself. Before, the plugin only worked on a Mac that already had it.

## 1.1.0 — 28 August 2026

**Toggle** works, so the On/Off buttons on control pages and dashboards switch a relay. Before, a toggle did nothing at all.

## 1.0.0 — 26 August 2026

The first version: hub, relay and command devices, learning buttons from the Plugins menu, and finding Broadlink devices on the network.
