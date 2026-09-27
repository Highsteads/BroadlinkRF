---
title: How it works
nav_order: 5
---

# How it works

You do not need to know any of this to use the plugin. It is here for anyone who likes to know what is going on.

## Pressing a button

A learned button is a recording of the radio signal the remote sends. When Indigo asks for a button, the plugin connects to the RM4 Pro over your home network and has it play the recording back. The plugin sends it three times to start with, a fifth of a second apart, because a radio signal can be missed and the appliance only needs to hear it once. You can change the number of times for each hub, or for a single device.

Nothing comes back over the radio. The hub has no way of knowing whether the appliance heard. A power meter on the appliance is how the plugin finds out.

## Following a power meter

A **Broadlink RF Relay** can be pointed at the smart plug or meter the appliance runs from. Whenever that meter reports a new reading, the plugin compares it with the **On above** setting — above it, the appliance is on, below it, off.

After Indigo presses a button, a meter often reports once or twice more before the appliance has acted on it, because it reports on its own timetable. So the plugin ignores readings that still disagree until the **Confirm within** time has passed. If the meter agrees in that time, the press is confirmed. If not, the reading wins and the log says the appliance did not respond.

If the reading crosses the line when Indigo has pressed nothing, someone has used the appliance's own remote or the appliance has switched itself, and the log says it was switched by something other than the plugin.

The plugin also looks at every relay's meter every 30 seconds, which is how it notices a meter that has stopped reporting.

## Watching the hub

An RM4 Pro that drops off the network gives no sign. It stops answering, and without the watchdog the first anyone knows is a button press that never arrives. I found this out when our living room access point restarted: every other device in the room reconnected within minutes, and the RM4 Pro sat silent for two hours and forty-two minutes until I pulled its plug, after which it took about ten minutes to come back.

So the plugin asks each hub whether it is there, as often as you choose in the hub's **Watchdog** settings. The hub is asked twice before the plugin decides it is missing, because one missed answer on Wi-Fi proves little.

- **The first time it does not answer**, the log has one error line saying so, and the device shows **unreachable** in red, so anything that watches for failed devices sees it too. The plugin remembers this even if it restarts, so it does not say it again.
- **When it answers again**, the red clears and the log says how long it was away.
- **If you have told it which switch or smart plug the hub runs from**, and the hub has been missing for the time you chose, the plugin switches that plug off for a few seconds. Indigo itself switches it back on, so the hub is not left without power if the plugin restarts part way through.
- **It waits 15 minutes between attempts**, because the hub takes about ten minutes to rejoin the network after losing power, and cutting it again sooner would interrupt that.
- **After the last attempt it stops**, and the log says the hub needs looking at, so a hub that has failed for good is not switched off and on all night.

The watchdog leaves a hub alone while it is learning a button or scanning for a frequency, and does not check hubs that are disabled in Indigo.
