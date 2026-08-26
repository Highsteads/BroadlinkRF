# Broadlink RF for Indigo

This plugin provides local-LAN control of Broadlink RM4 Pro RF commands.

## Design

- **Broadlink RM4 Pro** custom device: IP, port, default frequency, repeat count and code-store path.
- **Broadlink RF Command** custom device: select a stored command by name and send it from Indigo actions.
- **Broadlink RF Relay** relay device: map separate RF commands to Indigo On and Off, so it can be used by normal Indigo triggers and action groups.
- Plugin menu learning: choose the RM4 Pro, name the code, and watch the Indigo Event Log for the press/hold prompt.
- Plugin menu discovery: scan the local network and log Broadlink device addresses if the hub's DHCP address changes.
- Existing `broadlink_codes.json` captures are read automatically, including the legacy `hex` format.

The RM4 Pro is not a spectrum analyser. It can learn and replay compatible fixed-code RF remotes; rolling-code and encrypted devices remain unsupported.
