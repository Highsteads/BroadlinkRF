# Broadlink RF for Indigo

**Version:** 1.3.1

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
- **A watchdog on the hub** — an RM4 Pro says nothing when it drops off the network,
  so the plugin checks it on a timer instead. It reports the hub missing once, marks
  the device in error so it shows red, and says how long it was away when it returns.
  Point it at the switch or smart plug the hub runs on and it will cut the power to
  bring the hub back, which is the one thing known to work.
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

## Keeping the hub alive

An RM4 Pro that loses its access point does not always find its way back. It gives no
sign either — it simply stops answering, and the first you know is a command that never
arrives. The hub device's **Watchdog** section deals with both halves of that.

- **Check the hub every** — how often to ask it whether it is there. Five minutes suits
  most houses. Set it to Never and the watchdog does nothing.
- **Power-cycle using** — the switch or smart plug the RM4 Pro is plugged into. Leave it
  on *None* and the watchdog will tell you the hub is missing but will not try to fix it.
- **Cut power after** — how long the hub must be missing first. Ten minutes is enough to
  rule out a reboot or a brief radio problem.
- **Try at most** — after this many attempts the watchdog stops and leaves the hub alone,
  so a unit that has genuinely died is not switched off and on all night.

It allows fifteen minutes between attempts. One of these takes about ten minutes to
rejoin a network after losing power, so cycling sooner would interrupt the recovery it
is waiting for.

## Version history

- **v1.3.1** — a command that names no hub now looks for a hub that is actually in
  service. A device can either be told which hub to transmit through or leave it blank,
  and a blank one falls back to "there is only one hub, so use that". That count
  included hubs switched off in Indigo, so a spare sitting on a shelf made the count two
  and every blank command was refused while a perfectly good hub sat there; and a single
  hub taken out of service was handed back anyway, so the send failed as a network
  timeout that explained nothing. The watchdog had always paired the two checks. This
  one had not.
- **v1.3.0** — the hub is watched on a timer and can be recovered by cutting its power.
  Until now the plugin only ever spoke to the RM4 Pro when something asked it to
  transmit, so a hub that had fallen off the network was invisible until a command
  failed. Worse, the device looked healthy while it happened: Indigo refreshes a
  device's communication time on any state write, and the plugin writes an error state
  on every failed send, so the more consistently it failed the more recently it appeared
  to have been in touch. The hub device now carries a Watchdog section — see above.
- **v1.2.2** — the bundle carries the standard GitHub record. No behaviour change.
- **v1.2.1** — removed an unused import. No behaviour change.
- **v1.2.0** — ships a `requirements.txt`, so Indigo installs the `broadlink` package
  itself rather than only working on a machine that already happened to have it.
- **v1.1.0** — On/Off tiles work. Indigo passes a toggle straight through rather than
  resolving it into on or off, and without that branch every dashboard and control-page
  press was silently doing nothing.

## Acknowledgements

Built on [python-broadlink](https://github.com/mjg59/python-broadlink) by Mike Ryan
and Matthew Garrett, which does all the real work of speaking to the hardware. It is
MIT licensed, and this plugin would have been a great deal harder without it.

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
