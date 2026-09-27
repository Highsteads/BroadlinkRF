---
title: Your devices
nav_order: 4
---

# Your devices

The plugin has three kinds of device. Every state listed here can be used in a trigger or shown on a control page, under the name in the left-hand column.

## Broadlink RM4 Pro

The hub itself. You need one of these before anything else, and every other device sends its buttons through it.

The device list shows its **Connection State**:

| Connection State | What it means |
|---|---|
| **Configured** | The plugin has started the device but has not checked the hub yet. |
| **Connected** | The hub answered the last time the plugin asked, or has just sent a button. |
| **Unreachable** | The hub did not answer a check. The device list shows **unreachable** in red until it answers again. See [When something goes wrong](troubleshooting.md). |
| **Error** | The last attempt to send a button, learn one or diagnose the hub failed. **Last Error** says why. |
| **Learning** | The hub is listening for a button from a remote. |
| **Ready** | A learn has just finished or timed out. |
| **Stopped** | The device is disabled in Indigo, or the plugin has stopped. |

Its other states:

| Shown as | What it means |
|---|---|
| **Firmware Version** | The hub's firmware version, filled in by **Diagnose RM4 Pro**. |
| **RF Frequency** | The frequency in MHz from the hub's settings, or the one found by the last frequency scan or learn. |
| **Stored RF Code Count** | How many buttons the RF code store holds. |
| **Last Command** | The name of the last button sent through this hub, or the one last learned. |
| **Last Result** | What happened last, such as **Sent**, **Failed**, **Learned**, **Learn timed out** or **Diagnosis complete**. |
| **Last Error** | Why the last attempt failed. It is empty after a success. |
| **Last Sent At** | The date and time the hub last sent a button, such as `2026-09-21 19:05:10`. |
| **Sent Count** | How many buttons this hub has sent. |
| **Last Checked At** | The date and time of the watchdog's last check. |
| **Unreachable Since** | When the hub stopped answering. It is empty while the hub is answering. |
| **Recovery Attempts** | How many times the watchdog has cut the hub's power during the current outage. It goes back to 0 once the hub answers. |
| **Last Recovery At** | When the watchdog last cut the hub's power. |

## Broadlink RF Relay

For an appliance with an on and an off. It uses one learned button for on and another for off, and Indigo treats it like any other relay — you switch it with **Turn On**, **Turn Off** and **Toggle** from the device list, a control page, a schedule, a trigger or an action group.

The device list shows **On** or **Off**.

**Without a power meter**, that is only the last button the plugin pressed. The radio signal goes one way, so if someone uses the appliance's own remote, or the appliance misses the signal, Indigo does not know. A **Toggle** then goes by the last button pressed, so it can go the wrong way after someone has used the handset. Use **Turn On** or **Turn Off** when it matters which way it goes.

**With a power meter** — a smart plug or anything else in Indigo that reports the appliance's power in watts — the On or Off follows the reading instead:

- A press on the appliance's own remote shows in Indigo when the meter next reports, and the Event Log says the appliance was switched by something other than the plugin.
- After Indigo presses a button, the plugin waits for the meter to agree. If it has not agreed by the end of the confirmation time, the device goes back to what the meter reads, and the log says the appliance did not respond, with the reading.
- A **Toggle** goes by the reading, so it goes the right way even after someone used the handset.

I use this on the living room fire, whose plug reads half a watt in standby and 37 watts with the flame effect running, so an **On above** of 10 watts leaves plenty of room either side.

Its states:

| Shown as | What it means |
|---|---|
| **On / Off** | Whether the appliance is on or off — from the meter if it has one, otherwise the last button pressed. |
| **Last Command** | The name of the last button sent. |
| **Last Result** | **Ready** when the plugin starts, then **Sent** or **Failed** after each press. |
| **Last Error** | Why the last press failed. It is empty after a success. |
| **Last Sent At** | The date and time of the last press. |
| **Sent Count** | How many presses this device has sent. |
| **Measured Watts** | The meter's latest reading. |
| **Measured State** | **on**, **off** or **unknown**. It is **unknown** when there is no usable reading, so nothing that reads it mistakes the last button pressed for a measurement. |
| **Feedback Status** | What the meter says, in words — see below. |
| **Heavy Load** | True when the reading is above the **Heavy load above** setting, such as a fire's heater running. It stays false if that setting is blank. |

**Feedback Status** reads:

| Feedback Status | What it means |
|---|---|
| **On (measured)** or **Off (measured)** | The meter's reading agrees with the device. |
| **Waiting for on** or **Waiting for off** | A button has just been pressed and the plugin is waiting for the meter to agree. |
| **Did not turn on** or **Did not turn off** | The meter did not agree within the confirmation time. It stays until the reading changes. |
| **No reading** | The meter cannot be read — see below. |
| **Not configured** | The device has no power meter. |

The plugin stops trusting the meter if the meter is deleted, disabled in Indigo, in error, or has not reported for 15 minutes. The log says so once, **Measured State** becomes **unknown**, and the device goes back to showing the last button pressed until the reading returns, when the log says so again.

## Broadlink RF Command

For a single button that is not an on or an off. It holds one learned button, and you press it with the **Send RF Command** action — see [Actions and triggers](actions-and-triggers.md).

The device list shows its **Last Result** — **Ready** when the plugin starts, then **Sent** or **Failed** after each press.

| Shown as | What it means |
|---|---|
| **Selected RF Code** | The name of the button this device presses. |
| **Selected RF Frequency** | The frequency the button was learned at, in MHz. |
| **Last Result** | What happened on the last press. |
| **Last Error** | Why the last press failed. It is empty after a success. |
| **Last Sent At** | The date and time of the last press. |
| **Sent Count** | How many presses this device has sent. |
