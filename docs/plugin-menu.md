---
title: The plugin menu
nav_order: 8
---

# The plugin menu

These are under **Plugins → Broadlink RF**.

| Menu item | What it does |
|---|---|
| **Learn RF Command...** | Teaches a hub a button from your remote and saves it under a name. The [Learning buttons](learning.md) page goes through it step by step. |
| **Reload RF Code Store** | Reads the file of stored buttons again, and says in the log how many it holds. The plugin notices when the file changes, so you should rarely need this. |
| **List Stored RF Codes** | Writes every stored button to the log, with its frequency, its size and any note stored with it. |
| **Diagnose RM4 Pro Devices** | Connects to each hub in turn, including any disabled in Indigo, and writes its model, firmware version and number of stored buttons to the log. If a hub cannot be reached, the log says why. |
| **Discover Broadlink Devices** | Searches your network for five seconds and writes each Broadlink device it finds to the log, with its model and network address. If it finds nothing, run it again before you go looking for a fault, because a device on Wi-Fi can miss the search. |

**Reload RF Code Store** and **List Stored RF Codes** read the file named in **Plugins → Broadlink RF → Configure → RF code store**.
