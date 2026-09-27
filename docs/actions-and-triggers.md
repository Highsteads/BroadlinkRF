---
title: Actions and triggers
nav_order: 6
---

# Actions and triggers

## Switching a relay

A **Broadlink RF Relay** answers Indigo's standard **Turn On**, **Turn Off** and **Toggle**, wherever you use them — a control page, a schedule, a trigger or an action group. Each one presses the relay's on or off button.

If the press fails — the hub cannot be reached, say — the relay does not change, its **Last Result** shows **Failed**, and the Event Log says why.

Without a power meter, **Toggle** goes by the last button pressed, so after someone has used the appliance's own remote it can go the wrong way. Use **Turn On** or **Turn Off** in schedules and triggers where it matters which way it goes. With a power meter, **Toggle** goes by the reading.

**Send Status Request** re-reads the power meter there and then, and writes the result to the Event Log. A relay without a meter has nothing to ask, so it keeps its last state.

## The plugin's own actions

To use one of these, add an action, choose it from the **Broadlink RF** actions, and pick the device it applies to.

| Action | What it does |
|---|---|
| **Send RF Command** | For a **Broadlink RF Command** device. Presses its button. |
| **Send Code from RM4 Pro** | For a **Broadlink RM4 Pro** device. Presses any stored button you pick in **RF command**, without making a device for it. |
| **Learn RF Command...** | Learns a new button through a hub, in the same way as the menu item on the [Learning buttons](learning.md) page, with the same **Save as code name** and **Frequency (MHz)** boxes. The device keeps pressing the button chosen in its own settings, and its **Selected RF Code** goes on showing that button, so to use the new one, open the device and choose it. |
| **Scan RF Frequency** | Listens for a remote for up to 30 seconds and finds the frequency it uses. Hold a button on the remote near the hub while it runs. The log gives the frequency, and the hub's **RF Frequency** shows it. It does not change any setting. |
| **Reload RF Code Store** | Reads the hub's file of stored buttons again, and says in the log how many it holds. The plugin notices when the file changes, so you should rarely need this. |
| **Diagnose RM4 Pro** | Connects to the hub and writes its model, firmware version and number of stored buttons to the log, and fills in its **Firmware Version**. |

**Learn RF Command...**, **Scan RF Frequency**, **Reload RF Code Store** and **Diagnose RM4 Pro** work on a hub, or on a Command or Relay device, and then act on that device's hub.

## Triggers

The plugin has no triggers of its own. Instead, use Indigo's **Device State Changed** trigger on any of the states on the [Your devices](devices.md) page. For example:

- **Heavy Load** on a relay becoming true, to be told when a fire's heater comes on.
- **On / Off** on a relay with a power meter, to react when someone uses the appliance's own remote.
- **Connection State** on a hub becoming **Unreachable**, to send yourself a message when the hub drops off the network.
- **Feedback Status** on a relay, to catch a press the appliance did not respond to.
