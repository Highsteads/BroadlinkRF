---
title: Home
nav_order: 1
---

# Broadlink RF for Indigo

This plugin lets [Indigo](https://www.indigodomo.com) press the buttons on the radio remotes that came with things around the house — an electric fire or a set of blinds — through a **Broadlink RM4 Pro**. It talks to the RM4 Pro directly over your home network, so there is no Broadlink account involved and nothing goes out to the internet.

A good many appliances still come with a plain handheld remote and nothing else. You teach the RM4 Pro a button from that remote once, give it a name, and from then on Indigo can press it whenever you like.

## What it does for you

- **Learns the buttons** on a remote you already own, and keeps each one under a name you choose.
- **Presses a button** from Indigo, a control page, a schedule or a trigger.
- **Makes an appliance behave like a switch.** A **Broadlink RF Relay** device uses one button for on and another for off, so Indigo treats the appliance like any other light or plug.
- **Shows what the appliance is really doing** if it runs from a smart plug or anything else that reports its power in watts. The relay then follows the reading, so a press on the appliance's own remote shows up in Indigo, and a button press the appliance ignored is reported rather than shown as a success.
- **Keeps an eye on the RM4 Pro**, which gives no sign when it drops off the network. The plugin checks it on a timer, says so once when it goes missing, and can cut its power to bring it back.
- **Finds the RM4 Pro on your network** from the Plugins menu, which is the quickest way back if your router gives it a new address.

## What it cannot do

- **It only copies remotes that send the same signal every time** you press a button. Remotes that send a different signal each time — often called rolling-code remotes — cannot be copied.
- **It only learns radio remotes.** The RM4 Pro can also copy infrared remotes, but this plugin does not learn those.
- **Nothing comes back from the appliance over the radio.** On its own, a relay device in Indigo shows the last button the plugin pressed, not what the appliance is doing. If someone uses the original remote, Indigo does not know — unless the appliance runs from a power meter, as [Your devices](devices.md) explains.

## Where to go next

| If you want to... | Read |
|---|---|
| Install the plugin and add your RM4 Pro | [Getting started](getting-started.md) |
| Teach the RM4 Pro a button from your remote | [Learning buttons](learning.md) |
| Know what each device shows in Indigo | [Your devices](devices.md) |
| Understand what the plugin is doing behind the scenes | [How it works](how-it-works.md) |
| Press buttons from triggers, schedules and action groups | [Actions and triggers](actions-and-triggers.md) |
| Know what every setting does | [Settings](settings.md) |
| Know what each item in the Plugins menu does | [The plugin menu](plugin-menu.md) |
| Sort out a problem | [When something goes wrong](troubleshooting.md) |
| See what changed in each version | [Version history](changelog.md) |

## Download

The latest version is always on the [Releases page](https://github.com/Highsteads/BroadlinkRF/releases/latest).
