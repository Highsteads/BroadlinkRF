---
title: Settings
nav_order: 7
---

# Settings

## The plugin's settings

Open these with **Plugins → Broadlink RF → Configure**. They are starting values. Each hub device carries its own address, port, frequency, repeats and code store, and those are the ones it uses.

| Setting | What it does |
|---|---|
| **Default RM4 Pro IP** | A network address, used only by a hub device that has none of its own. The box cannot be left empty. `192.168.1.100` is filled in to start with. |
| **Default port** | The port number used by a hub device that has none of its own, 80 to start with. Leave it at 80 unless you know your hub uses another. |
| **Default RF frequency (MHz)** | The frequency filled in when you open **Learn RF Command...** from the Plugins menu, `433.92` to start with. Put `0` to have the hub find the frequency first. Anything else must be between 250 and 500. |
| **Default transmit repeats** | How many times a button is sent, when a hub device has no number of its own — 1, 2, 3 or 5, and 3 to start with. |
| **RF code store** | The file on the Mac that holds the learned buttons. **List Stored RF Codes** and **Reload RF Code Store** in the Plugins menu read this file. Keep it the same as the hub's **RF code store** unless you have a reason not to. |
| **Debug logging** | Adds more detail to the log, such as each check of the hub that goes unanswered. Only useful when chasing a problem. It takes effect the next time the plugin starts. |

## The hub's settings

Open these by double-clicking the **Broadlink RM4 Pro** device.

| Setting | What it does |
|---|---|
| **RM4 Pro IP address** | The hub's network address, such as `192.168.1.100`. It cannot be left empty. |
| **Port** | The port number the hub listens on, 80 to start with. Leave it at 80 unless you know otherwise. |
| **RF frequency (MHz)** | The hub's usual frequency, shown as its **RF Frequency** when the plugin starts. `433.92` to start with, `0`, or anything between 250 and 500. |
| **Transmit repeats** | How many times each button is sent — 1, 2, 3 or 5, and 3 to start with. More repeats help an appliance that sometimes misses a press. |
| **RF code store** | The file on the Mac that holds this hub's learned buttons. To start with it is `/Library/Application Support/Perceptive Automation/Python Scripts/broadlink_codes.json`. It cannot be left empty. |

### Watchdog

These are in the lower part of the same dialog. [How it works](how-it-works.md) explains what the watchdog does.

| Setting | What it does |
|---|---|
| **Check the hub every** | How often the plugin asks the hub whether it is there — 2, 5, 10 or 30 minutes, or **Never (watchdog off)**. It is 5 minutes to start with, which suits most houses. |
| **Power-cycle using** | The switch or smart plug the hub is plugged into. The list shows the on and off devices in Indigo, leaving out this plugin's own relays. Leave it on **None -- report only** and the watchdog tells you the hub is missing but does not try to fix it. |
| **Cut power after** | How long the hub must be missing before the plugin cuts its power — 5, 10, 15 or 30 minutes, and 10 to start with. Ten minutes is enough to rule out the hub restarting on its own or a brief Wi-Fi problem. |
| **Hold the power off for** | How long the power stays off — 5, 10, 20 or 30 seconds, and 10 to start with. Indigo switches it back on by itself. |
| **Try at most** | How many times the plugin cuts the power before it gives up and leaves the hub alone — once, twice or three times, and twice to start with. It waits 15 minutes between attempts, and starts counting again once the hub answers. |

**Cut power after**, **Hold the power off for** and **Try at most** only appear once you pick something in **Power-cycle using**. The time missing is counted from the first check the hub did not answer, and the power is only cut at a check, so with checks every 5 minutes and **Cut power after** at 10 minutes, the power goes off two checks after the hub first went quiet.

## A relay's settings

Open these by double-clicking a **Broadlink RF Relay** device.

| Setting | What it does |
|---|---|
| **RM4 Pro** | The hub that sends this relay's buttons. |
| **On RF command** | The learned button that switches the appliance on. The list shows each stored button with its frequency. |
| **Off RF command** | The learned button that switches it off. |
| **Repeat override** | How many times this relay's buttons are sent, if it should differ from the hub's number — 1, 2, 3 or 5. **Use RM4 default** leaves it to the hub. |

### Power meter

Everything in this part is optional. Leave **Power meter** on **None** and the relay shows the last button pressed. [Your devices](devices.md) explains what a meter gives you.

| Setting | What it does |
|---|---|
| **Power meter** | The smart plug or meter the appliance runs from. The list shows the devices in Indigo that report a power reading. |
| **Reading** | Which of that device's readings holds its power in watts. The plugin picks the likely one for you when you choose the meter, and the list shows each reading's value now, to help you check. |
| **On above (watts)** | The reading above which the appliance counts as on, 10 to start with. Set it well clear of what the appliance draws on standby — my fire reads half a watt on standby and 37 watts with the flame effect running. It must be more than 0. |
| **Confirm within (seconds)** | How long to wait after a press for the meter to agree, from 20 to 600 seconds, and 90 to start with. A Shelly plug reports about every 35 seconds, so 90 allows for two reports. |
| **Heavy load above (watts)** | Optional. Sets the relay's **Heavy Load** state when the reading passes it, such as 500 to see when a fire's heater is running. If you fill it in, it must be more than **On above**. |

## A command device's settings

Open these by double-clicking a **Broadlink RF Command** device.

| Setting | What it does |
|---|---|
| **RM4 Pro** | The hub that sends this device's button. |
| **RF command** | The learned button this device presses. |
| **Repeat override** | How many times the button is sent, if it should differ from the hub's number — 1, 2, 3 or 5. **Use RM4 default** leaves it to the hub. |
