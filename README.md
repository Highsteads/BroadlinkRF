# Broadlink RF for Indigo

**Press the buttons on your appliances' radio remotes from Indigo, through a Broadlink RM4 Pro on your home network.**

**Version:** 1.4.0 | **Author:** CliveS & Claude | **Needs:** Indigo 2025.1 or later and a Broadlink RM4 Pro

**[Read the full guide](https://highsteads.github.io/BroadlinkRF/)** — setting up, what everything means, and what to do when something goes wrong.

---

## What it does

A good many things in a house still come with a plain radio remote and nothing else — an electric fire, a set of blinds. This plugin lets [Indigo](https://www.indigodomo.com) press those buttons through a Broadlink RM4 Pro. It talks to the RM4 Pro directly over your home network, so there is no Broadlink account involved and nothing goes out to the internet.

- **Learns a button** from a remote you already own, and keeps it under a name you choose.
- **Presses it** from Indigo, a control page, a schedule or a trigger.
- **Makes an appliance behave like a switch.** A relay device uses one button for on and another for off, so schedules, triggers, action groups and control pages treat the appliance like any other switch.
- **Shows what the appliance is really doing** if it runs from a smart plug or anything else that reports its power. The relay then follows the reading, so a press on the appliance's own remote shows up in Indigo, and a press the appliance ignored is reported as ignored. I use it on the living room fire.
- **Keeps an eye on the hub.** An RM4 Pro gives no sign when it drops off the network, so the plugin checks it on a timer, says once when it goes missing, shows it red, and can switch off the plug it runs from for a few seconds to bring it back.
- **Finds the hub on your network** from the Plugins menu, which is the quickest way back if your router gives it a new address.

## What it works with

| In Indigo | What it is |
|---|---|
| **Broadlink RM4 Pro** | The hub itself, which sends the buttons |
| **Broadlink RF Relay** | An appliance with an on button and an off button |
| **Broadlink RF Command** | A single button, pressed with an action |

It copies radio remotes that send the same signal every time a button is pressed. Remotes that send a different signal each time — often called rolling-code remotes — cannot be copied, and this plugin does not learn infrared remotes.

## Installing

1. Go to the [Releases page](https://github.com/Highsteads/BroadlinkRF/releases/latest) and download `BroadlinkRF.indigoPlugin.zip`
2. Unzip the downloaded file — you will get `Broadlink RF.indigoPlugin`
3. Double-click `Broadlink RF.indigoPlugin` — Indigo will install it automatically

The first time the plugin starts, Indigo downloads the `broadlink` software it needs, so the Mac has to be on the internet for that.

## Setting it up

1. If you do not know the RM4 Pro's network address — the four numbers, such as `192.168.1.100`, that the Broadlink app shows — choose **Plugins → Broadlink RF → Discover Broadlink Devices** and look in the Event Log.
2. Create a **New Device**, choose **Broadlink RF** and **Broadlink RM4 Pro**, and type in the hub's address.
3. Choose **Plugins → Broadlink RF → Learn RF Command...**, name the button, click **Start Learning**, and press and hold the button on the remote near the hub when the Event Log says it is ready.
4. Create a **Broadlink RF Relay** device and choose the buttons for on and off. Switch it on from Indigo, and the appliance should respond.

The [full guide](https://highsteads.github.io/BroadlinkRF/) goes through each step, explains every setting, and covers what to do if something does not work.

## What's new

**v1.4.0** — A relay can follow a power meter on the appliance it switches, and its On or Off then comes from the reading instead of the last button pressed.
- Presses on the appliance's own remote show in Indigo.
- A press the appliance ignored is reported as ignored, with the reading.
- **Toggle** goes the right way even after someone used the handset.
- New **Measured Watts**, **Measured State**, **Feedback Status** and **Heavy Load** states for triggers and control pages.

**v1.3.2** — Notes in the code only. Nothing the plugin does changed.

**v1.3.1** — A device with no hub chosen now uses the one hub that is in service, rather than counting hubs that are disabled in Indigo.

Every version is listed in the [version history](https://highsteads.github.io/BroadlinkRF/changelog.html).

## Acknowledgements

Built on [python-broadlink](https://github.com/mjg59/python-broadlink) by Mike Ryan and Matthew Garrett, which does the work of talking to the hardware. It is MIT licensed, and this plugin would have been a great deal harder without it.

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
