# Broadlink RF for Indigo

Local-LAN control of Broadlink RM4 Pro RF commands, with no cloud account and no
bridge in the middle. Learn a code from a remote you already own, give it a name,
and send it from an Indigo action, trigger or control page.

It exists because a good many things in a house still come with a plain RF handset
and nothing else — an electric fire, a set of blinds, a garage remote. This plugin
lets Indigo press those buttons.

## What it gives you

- **Broadlink RM4 Pro** device — the hub itself: address, port, default frequency,
  repeat count and where the learned codes are kept.
- **Broadlink RF Command** device — one stored code by name, sent on demand.
- **Broadlink RF Relay** device — a normal Indigo relay that maps one code to On and
  another to Off, so schedules, triggers, action groups and control pages treat it
  like any other switch.
- **Learning from the plugin menu** — pick the hub, name the code, then follow the
  press-and-hold prompts in the Event Log.
- **Discovery from the plugin menu** — sweeps the local network and logs what it
  finds, which is the quickest way back when the hub's DHCP address moves.
- Existing `broadlink_codes.json` captures are read as they are, the older `hex`
  format included.

## What it cannot do

The RM4 Pro is a remote, not a spectrum analyser. It learns and replays fixed-code
RF remotes. Rolling-code and encrypted devices are beyond it, and no amount of
software will change that.

**RF is open loop.** Nothing comes back from the far end, so the device state in
Indigo is a record of what was sent, not a reading of what happened. If somebody
uses the original handset, Indigo will not know. Bear that in mind when you write
an automation that cares.

## Requirements

- Indigo 2025.1 or later
- A Broadlink RM4 Pro on the same network
- The `broadlink` Python package, which Indigo installs for you from the bundled
  `requirements.txt` the first time the plugin starts

## Installation

1. Go to the [Releases](https://github.com/Highsteads/BroadlinkRF/releases) page and
   download `BroadlinkRF.indigoPlugin.zip`.
2. Unzip it — you will get `Broadlink RF.indigoPlugin`.
3. Double-click `Broadlink RF.indigoPlugin` and Indigo will install it.

## Setting it up

Open the plugin's Configure dialog and enter the hub's address. If you do not know
it, run **Plugins → Broadlink RF → Discover Broadlink Devices** and watch the Event
Log.

Then create a **Broadlink RM4 Pro** device pointing at that address, learn your codes
through **Plugins → Broadlink RF → Learn RF Command**, and create a **Command** or
**Relay** device for each one. A Relay is usually what you want, because everything
else in Indigo already knows how to talk to a relay.

A note on discovery: Broadlink hubs answer a UDP broadcast, and UDP broadcast on
wifi is sent once, at the lowest rate, with nothing acknowledging it. A sweep that
finds nothing has not proved the hub is absent. Run it again before you go looking
for a fault.

## Acknowledgements

Built on [python-broadlink](https://github.com/mjg59/python-broadlink) by Mike Ryan
and Matthew Garrett, which does all the real work of speaking to the hardware. It is
MIT licensed, and this plugin would have been a great deal harder without it.

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
