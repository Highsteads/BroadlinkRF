####################
# Broadlink RF for Indigo
# Local-LAN RF control for Broadlink RM4 Pro devices.
# Version: 1.3.2
####################
#
# v1.3.0 (19-09-2026): WATCHDOG. The hub is now checked on a timer, and can be
# brought back by cutting its power.
#
# An RM4 Pro that falls off the network says nothing. It stops answering, and
# because this plugin only ever spoke to it on demand, the first symptom was a
# command that did not arrive. On 19-09-2026 the living room access point
# rebooted; every other device in the room re-associated within minutes and the
# RM4 Pro never did. It sat silent for two hours and forty-two minutes and came
# back ten minutes after its power was pulled by hand.
#
# Nothing could have noticed. Indigo refreshes lastSuccessfulComm on ANY state
# write, and this plugin writes lastError and lastResult on every FAILED send —
# so the more reliably it failed, the more recently it appeared to have
# communicated, and no check based on comm age could ever fire.
#
# The hub device now carries a Watchdog section: how often to check, and
# optionally which switch or smart plug the hub is plugged into. It reports the
# hub missing once (as an error, and on the device's own error state, so it
# shows red and a health monitor can see it), says how long it was away when it
# returns, and with a switch configured it cuts the power after a set delay.
# It allows fifteen minutes between attempts, because one of these takes about
# ten minutes to rejoin a network, and it stops after the configured number of
# attempts rather than cycling a dead unit all night.
#
# v1.2.2 (11-09-2026): GITHUBINFO. The bundle now carries the standard GitHub record
# (GithubInfo: GithubUser/GithubRepo), as the Indigo Domotics and community plugins do.
# No behaviour change.
#
# v1.2.1 (11-09-2026): removed an unused `import logging`, found the day the repo
# gained its ruff gate, CI workflow and version guard. No behaviour change.
#
# v1.2.0 (28-08-2026): ships a requirements.txt so Indigo installs the broadlink
# package itself. Until now the plugin imported it bare and only worked on a
# machine that already happened to have it, so a fresh install logged "the
# broadlink Python package is unavailable" and did nothing else. Also points
# CFBundleURLTypes at this plugin's own repository rather than upstream's.
#
# v1.1.0 (28-08-2026): actionControlDevice handles kDeviceAction.Toggle.
# Indigo does NOT resolve a toggle into TurnOn/TurnOff — it passes Toggle
# straight through, and a plugin without that branch does nothing at all: no
# RF, no state change, no error line. Every dashboard and control-page tile
# sends a toggle, so pressing the fire tile had been a silent no-op since the
# plugin shipped. An `else` now warns on any other action, because "called and
# did nothing" and "never called" look identical in an empty log.

try:
    import indigo
except ImportError:
    indigo = None

import ipaddress
import json
import os
import threading
from datetime import datetime


DEFAULT_CODE_STORE = "/Library/Application Support/Perceptive Automation/Python Scripts/broadlink_codes.json"


class Plugin(indigo.PluginBase):
    """Indigo plugin for Broadlink RM4 Pro fixed-code RF commands."""

    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs, **kwargs):
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)
        self.debug = self._as_bool(plugin_prefs.get("debugLogging", False))
        self._code_lock = threading.RLock()
        self._learn_lock = threading.Lock()
        self._codes_cache = {}
        self._code_mtimes = {}
        self._stopping = False
        self._broadlink = None
        self._last_probe = {}

    # ------------------------------------------------------------------
    # Indigo lifecycle and configuration
    # ------------------------------------------------------------------

    def startup(self):
        self._stopping = False
        self.debug = self._as_bool(self.pluginPrefs.get("debugLogging", False))
        try:
            import broadlink
            self._broadlink = broadlink
        except ImportError as exc:
            self._broadlink = None
            self.logger.error("The broadlink Python package is unavailable: %s", exc)
            return

        count = len(self._load_codes())
        self.logger.info("Broadlink RF started; %d stored RF code(s) available", count)

    def shutdown(self):
        self._stopping = True
        self.logger.info("Broadlink RF stopped")

    def validatePrefsConfigUi(self, values_dict):
        errors = indigo.Dict()
        host = str(values_dict.get("defaultHost", "")).strip()
        if not host:
            errors["defaultHost"] = "Enter the RM4 Pro IP address or hostname."
        else:
            try:
                ipaddress.ip_address(host)
            except ValueError:
                if any(ch.isspace() for ch in host):
                    errors["defaultHost"] = "Enter a valid IP address or hostname."

        self._validate_number(values_dict, "defaultPort", 1, 65535, errors, integer=True)
        self._validate_frequency(values_dict.get("defaultFrequency", ""), "defaultFrequency", errors)
        self._validate_repeat(values_dict.get("defaultRepeat", ""), "defaultRepeat", errors)
        if not str(values_dict.get("codeStorePath", "")).strip():
            errors["codeStorePath"] = "Enter a path for the RF code store."

        if errors:
            errors["showAlertText"] = "Please correct the highlighted Broadlink RF settings."
            return False, values_dict, errors
        return True, values_dict

    def validateDeviceConfigUi(self, values_dict, type_id, dev_id):
        errors = indigo.Dict()
        if type_id == "rm4Pro":
            host = str(values_dict.get("host", "")).strip()
            if not host:
                errors["host"] = "Enter the RM4 Pro IP address or hostname."
            self._validate_number(values_dict, "port", 1, 65535, errors, integer=True)
            self._validate_frequency(values_dict.get("frequency", ""), "frequency", errors)
            self._validate_repeat(values_dict.get("repeat", ""), "repeat", errors)
            if not str(values_dict.get("codeStorePath", "")).strip():
                errors["codeStorePath"] = "Enter a path for the RF code store."
        elif type_id in ("rfCommand", "rfRelay"):
            if not str(values_dict.get("hubDevice", "")).strip():
                errors["hubDevice"] = "Select a Broadlink RM4 Pro device."
            path = self._code_store_path_from_values(values_dict)
            if type_id == "rfCommand":
                self._validate_code_name(values_dict.get("codeName", ""), "codeName", path, errors)
            else:
                self._validate_code_name(values_dict.get("onCodeName", ""), "onCodeName", path, errors)
                self._validate_code_name(values_dict.get("offCodeName", ""), "offCodeName", path, errors)

        if errors:
            errors["showAlertText"] = "Please correct the highlighted Broadlink RF settings."
            return False, values_dict, errors
        return True, values_dict

    def validateActionConfigUi(self, values_dict, type_id, dev_id):
        errors = indigo.Dict()
        if type_id in ("learnRfCommand", "learnRfFromMenu"):
            name = str(values_dict.get("codeName", "")).strip()
            if not name or any(ch in name for ch in ",;\n"):
                errors["codeName"] = "Use a non-empty code name without commas or semicolons."
            self._validate_frequency(values_dict.get("frequency", ""), "frequency", errors, allow_blank=True)
        elif type_id == "sendHubCode" and not str(values_dict.get("codeName", "")).strip():
            errors["codeName"] = "Select an RF command."
        if errors:
            errors["showAlertText"] = "Please correct the highlighted action settings."
            return False, values_dict, errors
        return True, values_dict

    # ------------------------------------------------------------------
    # Device lifecycle and Indigo device actions
    # ------------------------------------------------------------------

    def deviceStartComm(self, dev):
        if dev.deviceTypeId == "rm4Pro":
            # A device created before these states existed does not have them,
            # and Indigo REFUSES the write with "state key <id> not defined
            # (ignoring update request)" -- an error per key, per pass, and no
            # watchdog state ever recorded. Adding them to Devices.xml is not
            # enough; the device has to be told its state list has changed, and
            # then re-fetched, because the object in hand still has the old one.
            dev = self._adopt_new_states(dev, self.WATCHDOG_STATES)
            # Seed the watchdog states with what they already hold rather than a
            # blank. A state only appears in Indigo once it has been written, but
            # unreachableSince is the latch that stops the plugin shouting about
            # the same outage twice -- clearing it on every restart would turn
            # "say it once" into "say it once per restart".
            was_missing = str(dev.states.get("unreachableSince") or "").strip()
            self._update_states(
                dev,
                connectionState="Unreachable" if was_missing else "Configured",
                configuredFrequency=self._hub_frequency(dev),
                codeCount=len(self._load_codes(dev)),
                lastCheckedAt=str(dev.states.get("lastCheckedAt") or ""),
                unreachableSince=was_missing,
                recoveryAttempts=self._state_int(dev, "recoveryAttempts"),
                lastRecoveryAt=str(dev.states.get("lastRecoveryAt") or ""),
            )
            if was_missing:
                self._set_error_state(dev, "unreachable")
        elif dev.deviceTypeId == "rfCommand":
            name = str(dev.pluginProps.get("codeName", ""))
            entry = self._load_codes(self._hub_for_command(dev)).get(name, {})
            self._update_states(
                dev,
                selectedCode=name,
                selectedFrequency=self._as_float(entry.get("frequency", 0.0), 0.0),
                lastResult="Ready",
            )
        elif dev.deviceTypeId == "rfRelay":
            self._update_states(dev, lastResult="Ready")

    def deviceStopComm(self, dev):
        if dev.deviceTypeId == "rm4Pro":
            self._update_states(dev, connectionState="Stopped")
        elif dev.deviceTypeId in ("rfCommand", "rfRelay"):
            self._update_states(dev, lastResult="Stopped")

    def deviceUpdated(self, orig_dev, new_dev):
        super().deviceUpdated(orig_dev, new_dev)

    # ------------------------------------------------------------------
    # Hub watchdog
    # ------------------------------------------------------------------
    #
    # An RM4 Pro that falls off the network says nothing whatsoever. It stops
    # answering, and the plugin only finds out when something asks it to
    # transmit -- so the first symptom is a command that does not arrive, and
    # on 19-09-2026 that hid a three-hour outage. The hub's access point had
    # rebooted; every other device in the room re-associated within minutes and
    # the RM4 Pro never did. It came back ten minutes after its power was cut
    # by hand.
    #
    # Worse, the device looked healthy throughout. Indigo refreshes
    # lastSuccessfulComm on ANY state write, and this plugin writes lastError
    # and lastResult on every FAILED send -- so the more consistently it failed,
    # the more recently it appeared to have communicated. Nothing watching comm
    # age could ever have noticed.
    #
    # So the watchdog asks the hub directly on a timer, records the answer where
    # a human and a health monitor can both see it, and -- given a switch to do
    # it with -- cuts the power, which is the only thing known to bring one of
    # these back.

    WATCHDOG_TICK_SECONDS = 30      # loop granularity; each hub keeps its own interval
    PROBE_TIMEOUT_SECONDS = 4
    PROBE_ATTEMPTS = 2              # one missed probe is not evidence of absence
    RECOVERY_GRACE_MINUTES = 15     # measured: an RM4 Pro takes ~10 min to rejoin

    def runConcurrentThread(self):
        try:
            while True:
                # The whole body is guarded. One bad pass must log and carry on,
                # never take the watchdog down and leave the hub unwatched.
                try:
                    self._watchdog_pass()
                except Exception:
                    self.logger.exception("Broadlink RF watchdog pass failed")
                # StopThread is raised out of self.sleep() and nowhere else, so
                # every wait in this loop has to go through it.
                self.sleep(self.WATCHDOG_TICK_SECONDS)
        except self.StopThread:
            pass

    def _watchdog_pass(self):
        if self._stopping or self._broadlink is None:
            return
        # A learn holds the hub in a listening mode of its own. Probing it
        # mid-learn would both disturb the capture and overwrite the
        # connectionState the learn is using to report progress.
        if self._learn_lock.locked():
            return
        now = self._monotonic()
        for dev in indigo.devices.iter("self"):
            if dev.deviceTypeId != "rm4Pro" or not dev.enabled:
                continue
            interval = self._as_int(dev.pluginProps.get("heartbeatMinutes", 5), 5)
            if interval <= 0:
                continue
            last = self._last_probe.get(dev.id, 0.0)
            if last and (now - last) < interval * 60:
                continue
            self._last_probe[dev.id] = now
            self._check_hub(dev)

    def _check_hub(self, hub_id_or_dev):
        # Always work from a freshly fetched device. The copy handed out by
        # devices.iter() is a snapshot, and the watchdog reads states it has
        # written on a previous pass.
        dev = self._refetch(hub_id_or_dev)
        if dev is None:
            return
        stamp = datetime.now()
        if self._hub_answers(dev):
            self._hub_answered(dev, stamp)
        else:
            self._hub_went_quiet(dev, stamp)

    def _hub_answers(self, dev):
        host = self._hub_host(dev)
        if not host:
            return False
        port = self._as_int(dev.pluginProps.get("port", self.pluginPrefs.get("defaultPort", 80)), 80)
        for attempt in range(max(1, self.PROBE_ATTEMPTS)):
            try:
                self._broadlink.hello(host, port=port, timeout=self.PROBE_TIMEOUT_SECONDS)
                return True
            except Exception as exc:
                self.logger.debug("Probe %d of %d for '%s' failed: %s",
                                  attempt + 1, self.PROBE_ATTEMPTS, dev.name, exc)
        return False

    def _hub_answered(self, dev, stamp):
        checked = stamp.strftime("%Y-%m-%d %H:%M:%S")
        since = str(dev.states.get("unreachableSince") or "").strip()
        if not since:
            self._update_states(dev, connectionState="Connected", lastCheckedAt=checked)
            return
        # It was missing and has come back. Say so with the outage length --
        # that is the number worth having, and nothing else records it.
        self._update_states(
            dev,
            connectionState="Connected",
            lastCheckedAt=checked,
            unreachableSince="",
            recoveryAttempts=0,
            lastError="",
        )
        self._set_error_state(dev, "")
        self.logger.info("'%s' is answering again after %s away.",
                         dev.name, self._describe_gap(since, stamp))

    def _hub_went_quiet(self, dev, stamp):
        checked = stamp.strftime("%Y-%m-%d %H:%M:%S")
        since = str(dev.states.get("unreachableSince") or "").strip()
        if not since:
            # First miss. Latch it in a DEVICE STATE rather than memory, so the
            # "say it once" survives a plugin restart instead of resetting and
            # shouting again.
            self._update_states(
                dev,
                connectionState="Unreachable",
                lastCheckedAt=checked,
                unreachableSince=checked,
                recoveryAttempts=0,
            )
            self._set_error_state(dev, "unreachable")
            self.logger.error(
                "'%s' has stopped answering at %s. Nothing can be sent over RF until it returns.",
                dev.name, self._hub_host(dev) or "its configured address")
            return

        self._update_states(dev, connectionState="Unreachable", lastCheckedAt=checked)
        self._attempt_recovery(dev, since, stamp)

    def _attempt_recovery(self, dev, since, stamp):
        plug_id = self._as_int(dev.pluginProps.get("recoveryPlug", 0), 0)
        if plug_id <= 0:
            return                                    # nothing to switch; reporting only
        max_attempts = self._as_int(dev.pluginProps.get("recoveryMaxAttempts", 2), 2)
        attempts = self._state_int(dev, "recoveryAttempts")
        if attempts >= max_attempts:
            return                                    # already given up, and already said so

        after = self._as_int(dev.pluginProps.get("recoveryAfterMinutes", 10), 10)
        down_minutes = self._minutes_between(since, stamp)
        if down_minutes is None or down_minutes < after:
            return

        # Leave a gap between attempts. One of these takes about ten minutes to
        # rejoin a network after losing power, so cycling again too soon would
        # interrupt the very recovery it is waiting for.
        last_recovery = str(dev.states.get("lastRecoveryAt") or "").strip()
        if last_recovery:
            gap = self._minutes_between(last_recovery, stamp)
            if gap is not None and gap < self.RECOVERY_GRACE_MINUTES:
                return

        plug = self._device_from_id(plug_id)
        if plug is None:
            self.logger.error(
                "'%s' cannot be power-cycled: the switch chosen for it (id %s) no longer exists.",
                dev.name, plug_id)
            return

        off_seconds = self._as_int(dev.pluginProps.get("recoveryOffSeconds", 10), 10)
        off_seconds = max(1, min(off_seconds, 60))
        try:
            # duration= schedules the switch-on with the SERVER, so the hub
            # cannot be left powered off if this plugin restarts mid-cycle.
            indigo.device.turnOff(plug.id, duration=off_seconds)
        except Exception as exc:
            self.logger.error("Could not power-cycle '%s' for '%s': %s", plug.name, dev.name, exc)
            return

        attempts += 1
        self._update_states(
            dev,
            recoveryAttempts=attempts,
            lastRecoveryAt=stamp.strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.logger.info(
            "'%s' has been missing for %s, so '%s' goes off for %d seconds to restart it "
            "(attempt %d of %d).",
            dev.name, self._describe_gap(since, stamp), plug.name, off_seconds,
            attempts, max_attempts)
        if attempts >= max_attempts:
            # Terminate, and say so once. A dead unit must not be cycled all night.
            self.logger.error(
                "'%s' has now been power-cycled %d time(s) without coming back. "
                "Leaving it alone -- it needs looking at.",
                dev.name, attempts)

    def switchable_devices(self, filter_str="", values_dict=None, type_id="", target_id=0):
        """Relay devices the watchdog could cut power with, for the hub's config dialog."""
        options = [("0", "None -- report only")]
        for dev in indigo.devices.iter("indigo.relay"):
            if dev.pluginId == self.pluginId:
                continue          # our own RF relays are one-way; they cannot cut mains
            options.append((str(dev.id), dev.name))
        return options

    # -- watchdog helpers ----------------------------------------------

    WATCHDOG_STATES = ("lastCheckedAt", "unreachableSince", "recoveryAttempts", "lastRecoveryAt")

    def _adopt_new_states(self, dev, keys):
        """Make sure a device carries `keys`, re-reading it if its list changed."""
        if all(key in dev.states for key in keys):
            return dev
        try:
            dev.stateListOrDisplayStateIdChanged()
        except Exception as exc:
            self.logger.debug("Could not refresh the state list for '%s': %s", dev.name, exc)
            return dev
        return self._refetch(dev) or dev

    def _refetch(self, dev_or_id):
        dev_id = getattr(dev_or_id, "id", dev_or_id)
        return self._device_from_id(dev_id)

    def _set_error_state(self, dev, message):
        """Show the fault on the device itself, so Indigo and any health monitor see it."""
        try:
            dev.setErrorStateOnServer(message)
        except Exception as exc:
            self.logger.debug("Could not set the error state on '%s': %s", dev.name, exc)

    @staticmethod
    def _minutes_between(stamp_text, now):
        try:
            then = datetime.strptime(str(stamp_text).strip(), "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            return None
        return max(0.0, (now.timestamp() - then.timestamp()) / 60.0)

    @classmethod
    def _describe_gap(cls, stamp_text, now):
        """A gap in the words a person uses, never a bare number of minutes."""
        minutes = cls._minutes_between(stamp_text, now)
        if minutes is None:
            return "an unknown time"
        minutes = int(round(minutes))
        if minutes < 1:
            return "less than a minute"
        if minutes == 1:
            return "1 minute"
        if minutes < 60:
            return "%d minutes" % minutes
        hours, rest = divmod(minutes, 60)
        hour_text = "1 hour" if hours == 1 else "%d hours" % hours
        if rest == 0:
            return hour_text
        return "%s and %s" % (hour_text, "1 minute" if rest == 1 else "%d minutes" % rest)

    def actionControlDevice(self, action, dev):
        """Provide normal Indigo On/Off actions for Broadlink RF Relay devices."""
        if dev.deviceTypeId != "rfRelay":
            return

        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            code_name = str(dev.pluginProps.get("onCodeName", ""))
            if self._send_from_device(dev, code_name):
                dev.updateStateOnServer("onOffState", True)
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            code_name = str(dev.pluginProps.get("offCodeName", ""))
            if self._send_from_device(dev, code_name):
                dev.updateStateOnServer("onOffState", False)
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            # Indigo does NOT resolve a toggle into TurnOn/TurnOff — it passes
            # kDeviceAction.Toggle straight through, and a plugin that does not
            # implement it simply does nothing. No RF, no state change, no error
            # line: the press is silently swallowed. That is what every dashboard
            # and control-page tile on this device was doing, because those send
            # a toggle rather than an explicit on/off.
            #
            # THE STATE WE FLIP FROM IS A BELIEF, NOT A READING. This relay is
            # one-way, so onOffState is only what was last transmitted. If the
            # fire was lit by its own handset the belief says off, and a toggle
            # will therefore send ON. That is inherent to a device with no
            # return path — use the explicit Turn On / Turn Off actions when you
            # need to ASSERT a state rather than flip one.
            turning_on = not dev.onState
            code_name  = str(dev.pluginProps.get(
                "onCodeName" if turning_on else "offCodeName", ""))
            if self._send_from_device(dev, code_name):
                dev.updateStateOnServer("onOffState", turning_on)
        elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
            self._update_states(dev, lastResult="RF devices do not report state; last command retained")
        else:
            # Anything else is a command this device cannot honour. Say so:
            # without this, "called and did nothing" and "never called at all"
            # look identical in an empty log, and they have different causes.
            self.logger.warning(
                f'"{dev.name}" received {action.deviceAction!r}, which an RF relay '
                f'cannot perform — ignored')

    # ------------------------------------------------------------------
    # Dynamic lists and menu dialogs
    # ------------------------------------------------------------------

    def hub_devices(self, filter_str="", values_dict=None, type_id="", target_id=0):
        # DELIBERATELY includes disabled hubs, unlike _watchdog_pass() and
        # _hub_for_command(). This is the picker: a hub switched off for the
        # afternoon must still be choosable, or configuring a device while its
        # hub is out of service becomes impossible. A command bound to a
        # disabled hub then fails at send time, which is the right place for it
        # to fail -- the user disabled the hub on purpose.
        return [(str(dev.id), dev.name) for dev in indigo.devices.iter("self")
                if dev.deviceTypeId == "rm4Pro"]

    def available_codes(self, filter_str="", values_dict=None, type_id="", target_id=0):
        hub = None
        values_dict = values_dict or {}
        selected_hub = values_dict.get("hubDevice", "")
        if selected_hub:
            hub = self._device_from_id(selected_hub)
        if hub is None and target_id:
            target = self._device_from_id(target_id)
            if target is not None:
                hub = target if target.deviceTypeId == "rm4Pro" else self._hub_for_command(target)
        options = []
        for name, entry in sorted(self._load_codes(hub).items()):
            frequency = entry.get("frequency", "")
            label = f"{name} ({frequency} MHz)" if frequency else name
            options.append((str(name), label))
        return options

    def getMenuActionConfigUiValues(self, menu_id):
        values = indigo.Dict()
        if menu_id == "learnRfFromMenu":
            hubs = self.hub_devices()
            if hubs:
                values["hubDevice"] = hubs[0][0]
            values["frequency"] = str(self.pluginPrefs.get("defaultFrequency", "433.92"))
        return values

    def learn_rf_from_menu(self, values_dict, menu_id):
        hub = self._device_from_id(values_dict.get("hubDevice"))
        if hub is None:
            return False, values_dict, indigo.Dict({"hubDevice": "Select an RM4 Pro device."})
        self._start_learning(
            hub,
            str(values_dict.get("codeName", "")).strip(),
            values_dict.get("frequency", ""),
        )
        return True

    def import_codes_from_menu(self):
        count = len(self._load_codes(force=True))
        self.logger.info("RF code store reloaded: %d code(s) available", count)

    def list_codes(self):
        codes = self._load_codes(force=True)
        if not codes:
            self.logger.warning("No RF codes are stored")
            return
        for name, entry in sorted(codes.items()):
            packet_hex = self._packet_hex(entry)
            self.logger.info(
                "RF code '%s': %s MHz, %d bytes, %s",
                name,
                entry.get("frequency", "unknown"),
                len(bytes.fromhex(packet_hex)) if packet_hex else 0,
                entry.get("note", "no note"),
            )

    def diagnose_hubs(self):
        # Every hub, disabled ones included: a diagnostic that silently omitted
        # a hub would answer the wrong question. Contrast _watchdog_pass() and
        # _hub_for_command(), which ACT and so must skip what is out of service.
        for hub in (dev for dev in indigo.devices.iter("self")
                    if dev.deviceTypeId == "rm4Pro"):
            self._diagnose_hub(hub)

    def discover_hubs(self):
        """Find Broadlink devices on the local network and log their addresses."""
        try:
            if self._broadlink is None:
                import broadlink
                self._broadlink = broadlink
            self.logger.info("Searching the local network for Broadlink devices...")
            found = self._broadlink.discover(timeout=5)
            if not found:
                self.logger.warning("No Broadlink devices were found on the local network")
                return
            for device in found:
                address = getattr(device, "host", ("unknown", 0))
                self.logger.info(
                    "Found Broadlink device: %s at %s:%s, type 0x%04x",
                    getattr(device, "model", "unknown"), address[0], address[1],
                    getattr(device, "devtype", 0),
                )
        except Exception as exc:
            self.logger.error("Broadlink discovery failed: %s", exc)

    # ------------------------------------------------------------------
    # Custom actions
    # ------------------------------------------------------------------

    def send_rf_command(self, action, dev):
        if dev.deviceTypeId != "rfCommand":
            return
        name = str(dev.pluginProps.get("codeName", ""))
        self._send_from_device(dev, name)

    def learn_rf_command(self, action, dev):
        hub = self._hub_for_command(dev)
        if hub is None:
            self.logger.error("No RM4 Pro selected for '%s'", dev.name)
            return
        props = getattr(action, "props", {})
        name = str(props.get("codeName", dev.pluginProps.get("codeName", ""))).strip()
        frequency = props.get("frequency", self._hub_frequency(hub))
        self._start_learning(hub, name, frequency, target_dev=dev)

    def scan_rf_frequency(self, action, dev):
        hub = dev if dev.deviceTypeId == "rm4Pro" else self._hub_for_command(dev)
        if hub is not None:
            self._start_scan(hub)

    def send_hub_code(self, action, dev):
        if dev.deviceTypeId != "rm4Pro":
            return
        name = str(getattr(action, "props", {}).get("codeName", "")).strip()
        self._send_code(hub=dev, code_name=name, target_dev=dev)

    def import_codes(self, action, dev):
        count = len(self._load_codes(dev if dev.deviceTypeId == "rm4Pro" else None, force=True))
        self.logger.info("RF code store reloaded: %d code(s) available", count)

    def diagnose_hub(self, action, dev):
        hub = dev if dev.deviceTypeId == "rm4Pro" else self._hub_for_command(dev)
        if hub is not None:
            self._diagnose_hub(hub)

    # ------------------------------------------------------------------
    # RF implementation
    # ------------------------------------------------------------------

    def _send_from_device(self, dev, code_name):
        if dev.deviceTypeId == "rm4Pro":
            hub = dev
        else:
            hub = self._hub_for_command(dev)
        if hub is None:
            self.logger.error("No Broadlink RM4 Pro is selected for '%s'", dev.name)
            self._update_states(dev, lastResult="Failed", lastError="No RM4 Pro selected")
            return False
        repeat = self._as_int(dev.pluginProps.get("repeatOverride", ""), 0)
        return self._send_code(hub, code_name, repeat=repeat or None, target_dev=dev)

    def _send_code(self, hub, code_name, repeat=None, target_dev=None):
        code_name = str(code_name).strip()
        codes = self._load_codes(hub)
        entry = codes.get(code_name)
        packet_hex = self._packet_hex(entry or {})
        if not packet_hex:
            message = f"No stored RF code named '{code_name}'"
            self.logger.error(message)
            self._update_states(target_dev or hub, lastResult="Failed", lastError=message)
            return False

        try:
            packet = bytes.fromhex(packet_hex)
            broadlink_device = self._connect(hub)
            count = repeat or self._hub_repeat(hub)
            for index in range(max(1, count)):
                broadlink_device.send_data(packet)
                if index + 1 < count:
                    self.sleep(0.20)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._update_states(
                hub,
                connectionState="Connected",
                lastCommand=code_name,
                lastResult="Sent",
                lastError="",
                lastSentAt=timestamp,
                sentCount=self._state_int(hub, "sentCount") + 1,
                codeCount=len(codes),
            )
            if target_dev is not None and target_dev.id != hub.id:
                self._update_states(
                    target_dev,
                    lastResult="Sent",
                    lastError="",
                    lastCommand=code_name,
                    lastSentAt=timestamp,
                    sentCount=self._state_int(target_dev, "sentCount") + 1,
                )
            self.logger.info("Sent Broadlink RF code '%s' at %s MHz (%d repeat(s))",
                             code_name, entry.get("frequency", "unknown"), count)
            return True
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            self.logger.error("Broadlink RF send failed for '%s': %s", code_name, message)
            self._update_states(hub, connectionState="Error", lastResult="Failed", lastError=message)
            if target_dev is not None and target_dev.id != hub.id:
                self._update_states(target_dev, lastResult="Failed", lastError=message)
            return False

    def _start_learning(self, hub, code_name, frequency, target_dev=None):
        code_name = str(code_name).strip()
        if not code_name:
            self.logger.error("RF learning needs a code name")
            return
        if self._learn_lock.locked():
            self.logger.warning("An RF learn or frequency scan is already running")
            return
        try:
            parsed_frequency = float(str(frequency).strip()) if str(frequency).strip() else 0.0
        except ValueError:
            self.logger.error("Invalid RF frequency: %s", frequency)
            return
        threading.Thread(
            target=self._learn_worker,
            args=(hub, code_name, parsed_frequency, target_dev),
            name="BroadlinkRFLearn",
            daemon=True,
        ).start()

    def _learn_worker(self, hub, code_name, frequency, target_dev):
        with self._learn_lock:
            try:
                device = self._connect(hub)
                if frequency <= 0:
                    device.sweep_frequency()
                    self.logger.info("RF frequency scan started. Hold the remote button near the RM4 Pro.")
                    deadline = self._monotonic() + 30
                    found = False
                    while self._monotonic() < deadline and not self._stopping:
                        self.sleep(1)
                        found, frequency = device.check_frequency()
                        if found:
                            break
                    if not found:
                        self.logger.error("RF frequency scan timed out")
                        return
                    self.logger.info("RF frequency found: %.3f MHz", frequency)

                device.find_rf_packet(frequency)
                self._update_states(hub, connectionState="Learning", configuredFrequency=frequency)
                self.logger.info(
                    "RF learning ready at %.3f MHz. Press and hold the SAME remote button for 2–3 seconds now.",
                    frequency,
                )
                packet = None
                deadline = self._monotonic() + 30
                while self._monotonic() < deadline and not self._stopping:
                    self.sleep(1)
                    try:
                        candidate = device.check_data()
                    except Exception:
                        continue
                    if candidate and len(candidate) >= 20:
                        packet = bytes(candidate)
                        break
                if packet is None:
                    self.logger.error("RF learning timed out; no usable packet was captured")
                    self._update_states(hub, connectionState="Ready", lastResult="Learn timed out")
                    return

                packet_hex = packet.hex()
                codes = self._load_codes(hub, force=True)
                codes[code_name] = {
                    "frequency": round(float(frequency), 3),
                    "hex": packet_hex,
                    "packet": packet_hex,
                    "bytes": len(packet),
                    "learned": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "valid": True,
                }
                self._save_codes(self._code_store_path(hub), codes)
                self._load_codes(hub, force=True)
                self._update_states(
                    hub,
                    connectionState="Ready",
                    configuredFrequency=float(frequency),
                    codeCount=len(codes),
                    lastCommand=f"Learned {code_name}",
                    lastResult="Learned",
                    lastError="",
                )
                if target_dev is not None:
                    self._update_states(
                        target_dev,
                        selectedCode=code_name,
                        selectedFrequency=float(frequency),
                        lastResult="Learned",
                        lastError="",
                    )
                self.logger.info("RF code '%s' learned: %.3f MHz, %d bytes", code_name, frequency, len(packet))
            except Exception as exc:
                self.logger.exception("Broadlink RF learning failed: %s", exc)
                self._update_states(hub, connectionState="Error", lastResult="Learn failed", lastError=str(exc))

    def _start_scan(self, hub):
        if self._learn_lock.locked():
            self.logger.warning("An RF learn or frequency scan is already running")
            return
        threading.Thread(target=self._scan_worker, args=(hub,), name="BroadlinkRFScan", daemon=True).start()

    def _scan_worker(self, hub):
        with self._learn_lock:
            try:
                device = self._connect(hub)
                device.sweep_frequency()
                self.logger.info("RF frequency scan started. Hold a remote button near the RM4 Pro.")
                deadline = self._monotonic() + 30
                while self._monotonic() < deadline and not self._stopping:
                    self.sleep(1)
                    found, frequency = device.check_frequency()
                    if found:
                        self._update_states(hub, configuredFrequency=float(frequency), lastResult="Frequency found")
                        self.logger.info("RF frequency found: %.3f MHz", frequency)
                        return
                self.logger.warning("RF frequency scan timed out")
                self._update_states(hub, lastResult="Frequency scan timed out")
            except Exception as exc:
                self.logger.exception("Broadlink RF frequency scan failed: %s", exc)

    # ------------------------------------------------------------------
    # Storage, connection and state helpers
    # ------------------------------------------------------------------

    def _connect(self, hub):
        if self._broadlink is None:
            import broadlink
            self._broadlink = broadlink
        host = self._hub_host(hub)
        port = self._as_int(hub.pluginProps.get("port", self.pluginPrefs.get("defaultPort", 80)), 80)
        device = self._broadlink.hello(host, port=port, timeout=5)
        if not device.auth():
            raise RuntimeError("Broadlink authentication failed; check the app lock setting")
        return device

    def _diagnose_hub(self, hub):
        try:
            device = self._connect(hub)
            firmware = device.get_fwversion()
            self._update_states(
                hub,
                connectionState="Connected",
                firmwareVersion=str(firmware),
                codeCount=len(self._load_codes(hub)),
                lastResult="Diagnosis complete",
                lastError="",
            )
            self.logger.info(
                "RM4 Pro '%s': %s, type 0x%04x, firmware %s, %d RF code(s)",
                hub.name, device.model, device.devtype, firmware, len(self._load_codes(hub)),
            )
        except Exception as exc:
            self.logger.error("RM4 Pro diagnosis failed for '%s': %s", hub.name, exc)
            self._update_states(hub, connectionState="Error", lastResult="Diagnosis failed", lastError=str(exc))

    def _load_codes(self, hub=None, force=False, path=None):
        path = os.path.expanduser(path) if path else self._code_store_path(hub)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = None
        with self._code_lock:
            if not force and path in self._codes_cache and self._code_mtimes.get(path) == mtime:
                return dict(self._codes_cache[path])
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if not isinstance(data, dict):
                    raise ValueError("the JSON root is not an object")
            except FileNotFoundError:
                data = {}
            except Exception as exc:
                self.logger.error("Could not read RF code store %s: %s", path, exc)
                data = {}
            self._codes_cache[path] = data
            self._code_mtimes[path] = mtime
            return dict(data)

    def _save_codes(self, path, codes):
        parent = os.path.dirname(path) or "."
        os.makedirs(parent, exist_ok=True)
        temporary = f"{path}.tmp.{os.getpid()}"
        with self._code_lock:
            try:
                with open(temporary, "w", encoding="utf-8") as handle:
                    json.dump(codes, handle, indent=2)
                    handle.write("\n")
                os.replace(temporary, path)
                self._codes_cache[path] = dict(codes)
                self._code_mtimes[path] = os.path.getmtime(path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)

    def _code_store_path(self, hub=None):
        if hub is not None:
            value = hub.pluginProps.get("codeStorePath", "")
            if str(value).strip():
                return os.path.expanduser(str(value).strip())
        value = self.pluginPrefs.get("codeStorePath", DEFAULT_CODE_STORE)
        return os.path.expanduser(str(value).strip() or DEFAULT_CODE_STORE)

    def _code_store_path_from_values(self, values_dict):
        value = values_dict.get("codeStorePath", "")
        if str(value).strip():
            return os.path.expanduser(str(value).strip())
        selected_hub = self._device_from_id(values_dict.get("hubDevice", ""))
        if selected_hub is not None and selected_hub.deviceTypeId == "rm4Pro":
            return self._code_store_path(selected_hub)
        return self._code_store_path()

    def _hub_for_command(self, dev):
        value = dev.pluginProps.get("hubDevice", "")
        hub = self._device_from_id(value)
        if hub is not None and hub.deviceTypeId == "rm4Pro":
            return hub
        # Count USABLE hubs, not every hub that exists. The watchdog already
        # pairs the type with `enabled`; this fallback did not, so a disabled
        # spare made the count two and the lone working hub was refused, while
        # a single disabled hub was returned and the send then failed at the
        # network layer instead of saying why (20-09-2026).
        hubs = [item for item in indigo.devices.iter("self")
                if item.deviceTypeId == "rm4Pro" and item.enabled]
        return hubs[0] if len(hubs) == 1 else None

    @staticmethod
    def _device_from_id(value):
        try:
            return indigo.devices[int(value)]
        except (TypeError, ValueError, KeyError):
            return None

    def _hub_host(self, hub):
        return str(hub.pluginProps.get("host", self.pluginPrefs.get("defaultHost", ""))).strip()

    def _hub_frequency(self, hub):
        return self._as_float(hub.pluginProps.get("frequency", self.pluginPrefs.get("defaultFrequency", 433.92)), 433.92)

    def _hub_repeat(self, hub):
        return self._as_int(hub.pluginProps.get("repeat", self.pluginPrefs.get("defaultRepeat", 3)), 3)

    @staticmethod
    def _packet_hex(entry):
        if not isinstance(entry, dict):
            return ""
        return str(entry.get("packet") or entry.get("hex") or "").strip()

    def _update_states(self, dev, **values):
        if dev is None:
            return
        try:
            dev.updateStatesOnServer([{"key": key, "value": value} for key, value in values.items()])
        except Exception as exc:
            self.logger.debug("Could not update '%s' states: %s", dev.name, exc)

    @staticmethod
    def _state_int(dev, key):
        try:
            return int(dev.states.get(key, 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _as_bool(value):
        return str(value).lower() in ("true", "yes", "1", "on")

    @staticmethod
    def _as_int(value, default):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_float(value, default):
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _monotonic():
        import time
        return time.monotonic()

    @staticmethod
    def _validate_number(values_dict, field_id, minimum, maximum, errors, integer=False):
        value = values_dict.get(field_id, "")
        try:
            number = int(str(value).strip()) if integer else float(str(value).strip())
            if not minimum <= number <= maximum:
                raise ValueError
        except (TypeError, ValueError):
            errors[field_id] = f"Enter a value from {minimum} to {maximum}."

    @classmethod
    def _validate_frequency(cls, value, field_id, errors, allow_blank=False):
        if allow_blank and not str(value).strip():
            return
        try:
            frequency = float(str(value).strip())
            if frequency != 0 and not 250 <= frequency <= 500:
                raise ValueError
        except (TypeError, ValueError):
            errors[field_id] = "Enter 0, 315, 433.92, or another frequency from 250–500 MHz."

    @staticmethod
    def _validate_repeat(value, field_id, errors):
        try:
            if int(str(value).strip()) not in (1, 2, 3, 5):
                raise ValueError
        except (TypeError, ValueError):
            errors[field_id] = "Choose 1, 2, 3, or 5 repeats."

    def _validate_code_name(self, value, field_id, path, errors, optional=False):
        name = str(value or "").strip()
        if not name and optional:
            return
        if not name:
            errors[field_id] = "Select an RF code."
        elif name not in self._load_codes(force=False, path=path):
            errors[field_id] = "This RF code is not present in the code store."
