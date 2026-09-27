---
title: When something goes wrong
nav_order: 9
---

# When something goes wrong

Each section starts with what you see, then what it means and what to do.

## The hub shows "unreachable"

The hub did not answer the watchdog's last check, and the Event Log has an error line saying it has stopped answering. Nothing can be sent until it returns.

- Check it has power, and that it is on your Wi-Fi in the Broadlink app.
- If your router may have given it a new address, run **Plugins → Broadlink RF → Discover Broadlink Devices**, and put the address it finds into the hub device's **RM4 Pro IP address**.
- If the hub stays away after your Wi-Fi has had a problem, unplug it for ten seconds and plug it back in. It takes about ten minutes to rejoin the network. To have the plugin do this for you, choose the plug it runs from in **Power-cycle using** in the hub's settings.

When it answers again, the red clears by itself and the log says how long it was away.

## The log says the hub has been power-cycled and is being left alone

The plugin cut the hub's power as many times as **Try at most** allows, and the hub still did not come back, so it has stopped trying. Have a look at the hub itself — its power supply, its Wi-Fi, and whether the Broadlink app can see it. Once it answers again, the count starts afresh.

## A button press does nothing

Look at the device's **Last Result** and **Last Error**, and at the Event Log.

- **Last Result says Sent** — the hub sent the button, but the appliance did not act on it. Move the hub closer to the appliance, or raise **Repeat override** on the device so the button is sent more times. If it never works, learn the button again.
- **The log says the send failed** — the hub could not be reached. See the first section above.
- **The log says there is no stored RF code of that name** — the button is not in the code store any more, or the device is reading a different file. Open the device and choose the button again, or learn it again.
- **The log says no RM4 Pro is selected** — open the device and choose the hub in **RM4 Pro**.

## The log says Broadlink authentication failed

The hub refused the plugin, and the log line tells you to check the app lock setting. The Broadlink app can lock a device so that only the app controls it. Unlock it in the Broadlink app, then try again.

## Learning a button times out

The hub heard nothing it could use within 30 seconds.

- Hold the remote close to the hub, and press and hold the button for two to three seconds when the log says learning is ready, not before.
- If you are not sure of the frequency, learn again with the **Frequency (MHz)** box empty or `0`, so the hub finds it first.
- Some remotes send a different signal every time, and the hub cannot copy those.

## The log says "An RF learn or frequency scan is already running"

Only one can run at a time. Wait up to a minute for the first to finish or time out, then try again.

## A relay says "Did not turn on" or "Did not turn off"

The plugin pressed the button, but the power meter did not agree within the **Confirm within** time, so the relay now shows what the meter reads. The appliance most likely missed the signal — try again, and if it keeps happening, raise **Repeat override** or move the hub closer. If the appliance did respond but its meter reports slowly, raise **Confirm within**.

## The log says a relay "can no longer read its power meter"

The meter has been deleted, disabled in Indigo, is in error, or has not reported for 15 minutes. Until it reports again, the relay shows the last button pressed, and its **Measured State** is **unknown**. The log says so when the meter is back.

## A relay's On or Off is wrong after someone used the appliance's remote

Without a power meter, the plugin cannot know about presses on the appliance's own remote. Give the relay a power meter if the appliance runs from one, and use **Turn On** or **Turn Off** rather than **Toggle** where it matters which way it goes.

## A device dialog says "This RF code is not present in the code store"

The button chosen is not in the hub's code store file. Pick another from the list, or check the hub's **RF code store** points at the file you learned your buttons into.

## The log says "The broadlink Python package is unavailable"

The plugin could not load the free software it uses to talk to the hub. Indigo downloads it the first time the plugin starts, which needs the Mac to be on the internet. Once it is, restart the plugin.

## Still stuck?

Choose **Plugins → Broadlink RF → Diagnose RM4 Pro Devices**, copy the lines it writes to the Event Log, and post them on the [Indigo forum](https://forums.indigodomo.com) with a description of what you see. You can also [raise an issue on GitHub](https://github.com/Highsteads/BroadlinkRF/issues).
