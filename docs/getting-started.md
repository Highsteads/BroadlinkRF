---
title: Getting started
nav_order: 2
---

# Getting started

You only do this once. Learning each button comes after, on the [Learning buttons](learning.md) page.

## What you need

- Indigo 2025.1 or later, on a Mac that is on the same home network as the RM4 Pro.
- A **Broadlink RM4 Pro** already joined to your Wi-Fi, which you do with the Broadlink app when you first unbox it.
- The RM4 Pro's **network address** — the four numbers separated by dots, such as `192.168.1.100`. The Broadlink app shows it in the device's settings, and your router's list of connected devices shows it too. If you cannot find it, the plugin can search for it, as step 3 below explains.
- The remote for each appliance you want Indigo to control.

It helps to ask your router to keep giving the RM4 Pro the same address, which most routers call a **reserved address** or **DHCP reservation**. The plugin reaches the hub by its address, so if the address changes, the hub device has to be told the new one.

The plugin also needs a small piece of free software called `broadlink`, which does the work of talking to the hub. Indigo downloads and installs it by itself the first time the plugin starts.

## 1. Install the plugin

1. Go to the [Releases page](https://github.com/Highsteads/BroadlinkRF/releases/latest) and download `BroadlinkRF.indigoPlugin.zip`
2. Unzip the downloaded file — you will get `Broadlink RF.indigoPlugin`
3. Double-click `Broadlink RF.indigoPlugin` — Indigo will install it automatically

Indigo asks whether to enable the plugin. Say yes. The Event Log then has a line saying Broadlink RF has started, with the number of stored buttons it found.

## 2. Check the plugin's settings

Open **Plugins → Broadlink RF → Configure**. These are starting values, and each hub device carries its own address and settings, so you can leave them as they are and click **Save**. Every setting is explained on the [Settings](settings.md) page.

## 3. Find the RM4 Pro, if you need to

Choose **Plugins → Broadlink RF → Discover Broadlink Devices**. The plugin searches your network for five seconds, and the Event Log lists each Broadlink device it finds with its model and address.

If it finds nothing, run it again before you go looking for a fault. The search is a single call to everything on the network, and a device on Wi-Fi can miss it.

## 4. Add the RM4 Pro to Indigo

1. In Indigo, choose **New Device**.
2. Set **Type** to **Broadlink RF**, then pick **Broadlink RM4 Pro**.
3. Type the hub's address into **RM4 Pro IP address**.
4. Leave the other settings as they are for now. The **Watchdog** part of the dialog is explained on the [Settings](settings.md) page, and checking the hub every five minutes is already switched on.
5. Click **Save**.

## 5. Check it works

Choose **Plugins → Broadlink RF → Diagnose RM4 Pro Devices**. The plugin connects to the hub, and the Event Log has a line giving its model, its firmware version and the number of buttons stored. The hub's **Connection State** in the device list changes to **Connected**.

If the log says the diagnosis failed instead, the [When something goes wrong](troubleshooting.md) page goes through the usual causes.

## 6. Learn your first button

Now go on to [Learning buttons](learning.md), which covers teaching the hub a button and making a device that presses it.
