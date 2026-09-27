---
title: Learning buttons
nav_order: 3
---

# Learning buttons

The RM4 Pro copies a button by listening to it. You hold the remote close to the hub, press the button, and the plugin saves what the hub heard under a name you choose. Each saved button is called an **RF code** in the plugin's dialogs.

## Teach the hub a button

1. Choose **Plugins → Broadlink RF → Learn RF Command...**
2. Pick the hub in **RM4 Pro**.
3. Type a name for the button in **Save as code name**, such as `fire_on`. Keep commas and semicolons out of it.
4. Leave **Frequency (MHz)** at `433.92` if you know the remote uses that frequency. If you do not know, clear the box or put `0`, and the hub finds the frequency first.
5. Click **Start Learning**.
6. Watch the Event Log. When it says learning is ready, **press and hold the button on the remote for two to three seconds**, close to the hub.
7. The log then says the code has been learned, with its frequency and size.

If you left the frequency blank or put `0`, the log first says a frequency scan has started. Hold a button near the hub until the log gives the frequency it found, then carry on from step 6 when it says learning is ready.

The plugin waits 30 seconds for each step. If nothing arrives in that time, the log says learning timed out, and you can start again.

Only one learn or frequency scan can run at a time. If you start a second, the log says one is already running.

If you learn a button under a name that is already stored, the new one replaces the old.

For an appliance you want to switch on and off, learn both buttons — `fire_on` and `fire_off`, say. If the remote has a single button that does both, learn that once.

## Make a device that presses it

Each learned button can be used in two ways. Pick the one that fits the appliance.

### A Broadlink RF Relay — for anything with an on and an off

This is usually what you want, because everything else in Indigo already knows how to switch a relay.

1. Choose **New Device**, set **Type** to **Broadlink RF**, and pick **Broadlink RF Relay**.
2. Pick the hub in **RM4 Pro**.
3. Pick the button for on in **On RF command**, and the button for off in **Off RF command**. For a remote with one button that does both, pick the same button twice.
4. Click **Save**.

The device now answers Indigo's usual **Turn On**, **Turn Off** and **Toggle**.

If the appliance runs from a smart plug or anything else that reports its power, fill in the **Power meter** part of the dialog too. The [Your devices](devices.md) page explains what that gives you, and [Settings](settings.md) explains each box.

### A Broadlink RF Command — for a single button

For a single button that is not an on or an off, such as a blind's stop button, use a command device.

1. Choose **New Device**, set **Type** to **Broadlink RF**, and pick **Broadlink RF Command**.
2. Pick the hub in **RM4 Pro**, and the button in **RF command**.
3. Click **Save**.

You press it with the **Send RF Command** action, as [Actions and triggers](actions-and-triggers.md) explains.

## Check it works

Switch the relay on from Indigo's device list, or run the command device's **Send RF Command** action. The appliance should respond, and the Event Log has a line saying which code was sent, at what frequency, and how many times.

If the appliance does nothing, the [When something goes wrong](troubleshooting.md) page has what to try.

## Where the buttons are kept

Every learned button goes into one file on the Mac, the **RF code store**. To start with it is:

`/Library/Application Support/Perceptive Automation/Python Scripts/broadlink_codes.json`

The plugin reads the file again whenever it changes. Keep a copy of it somewhere safe, because relearning every button takes a while.

If you already have a file of Broadlink captures in this format, point the plugin at it in the settings and it reads the codes as they are, the older format included.
