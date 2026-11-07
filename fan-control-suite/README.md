# iMac Fan Control Suite — iMac10,1 (2009)

[Magyar dokumentáció / Hungarian guide](README.hu.md)

> **Experimental, machine-specific project.** Developed for one late-2009 iMac reporting DMI `iMac10,1` with Ubuntu MATE 24.04. **The four scripts in `scripts/` are byte-for-byte synchronized from the owner's working iMac ZIP export dated 2026-11-07.** The systemd unit and desktop autostart entries remain templates, not exported system files. The code contains hardware-specific paths and assumptions; **it is not a universal unattended installer**.

## Why it exists

This iMac was upgraded with an SSD, and the original optical-drive (ODD) thermal-sensor arrangement was changed: the ODD sensing lead/probe was moved toward/on the SSD during the conversion. On this particular machine the ODD temperature channel subsequently appeared missing/invalid to Linux (e.g. SMC readings of `-127 °C` / `-128 °C`). Its behavior may differ from another iMac whose sensor wiring remains connected and working.

A missing temperature sensor can make the Apple SMC / ODD fan behave unexpectedly, including unnecessary high RPM. Simply forcing a fixed quiet RPM would be unsafe: it removes the thermal response needed to cool the modified chassis.

**The goal is not to disable protection.** The suite substitutes a conservative, multi-sensor software-driven thermal policy for the ODD fan, while leaving the CPU and HDD fans under firmware automatic control with optional *upward-only* minimum-RPM boosts.

## What the suite contains

| Component | Source | Function |
|---|---|---|
| Cooling daemon | [`scripts/imac-odd-fan.py`](scripts/imac-odd-fan.py) | Reads Apple SMC + CPU core sensors; controls ODD RPM; raises HDD/CPU minimum RPM only |
| Dark GUI | [`scripts/imac-fan-control.py`](scripts/imac-fan-control.py) | Live temperatures, three fan readings, response-boost sliders, four-minute history |
| MATE panel indicator | [`scripts/imac-panel-monitor.py`](scripts/imac-panel-monitor.py) | GPU temperature in the top panel; drop-down of other readings |
| GUI launcher | [`scripts/imac-fan-suite.sh`](scripts/imac-fan-suite.sh) | Starts GUI + panel indicator without duplicates |
| systemd example | [`systemd/imac-odd-fan.service`](systemd/imac-odd-fan.service) | Cooling daemon at system start (independent of login) |
| desktop example | [`desktop/imac-fan-suite.desktop`](desktop/imac-fan-suite.desktop) | GUI components at MATE login |

The machine's working dashboard uses a macOS-inspired dark layout and upward-only fan response controls. The panel indicator's dropdown still contains some Hungarian labels in this exact export. The panel display and main window are separate processes; the cooling service stays running when both are closed.

## Thermal model

**Read-only inputs:** GPU `TG0D/TG0H/TG0P`, chipset `TN0H`, PSU `Tp2H`, selected board/CPU sensors, and the Linux `coretemp` driver. Invalid SMC sentinel values are filtered.

- **ODD fan:** manual RPM output controlled by the daemon. Its baseline is the maximum demand from independent GPU, chipset, and PSU stepped curves. If any required ODD input disappears, the daemon requests maximum ODD RPM.
- **HDD fan:** firmware automatic mode retained; software may increase `fan2_min` above the verified baseline, never decrease it. The reference boost uses thermal proxies from the enclosure because it does **not** read the drive's internal SMART temperature.
- **CPU fan:** firmware automatic mode retained; software may increase `fan3_min` above the verified baseline, never decrease it.
- **0% sliders:** no additional acceleration over the ODD thermal baseline or factory HDD/CPU behavior. Higher percentages impose only more cooling.
- **Charts:** visualize the requested RPM *floor* or modeled ODD target; the firmware's actual HDD/CPU RPM may be higher than the requested minimum.

On the tested iMac the fan order was **1=ODD, 2=HDD, 3=CPU**, with reported SMC minimums **900, 1100 and 940 RPM**. **These numbers are examples from one machine, not safe universal defaults.** The exact exported daemon does **not** validate fan labels at runtime; verify every label and RPM limit manually before installing on another machine.

## Safe inspection before attempting a port

```bash
cat /sys/class/dmi/id/product_name
ls /sys/devices/platform/applesmc.*
sensors
for f in /sys/devices/platform/applesmc.*/fan{1,2,3}_{label,min,max,manual,input}; do echo "$f: $(cat "$f")"; done
```

Use the commands above as *read-only inspection*. The daemon requires root privileges to write sysfs files. **Do not install it unchanged** on another iMac model, a machine without the SSD/ODD modification, or one whose sensor wiring differs.

### UI dependencies (Ubuntu MATE 24.04)

```bash
sudo apt install python3 python3-tk python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

For the look shown in the screenshots, the Inter font and WhiteSur dark desktop theme are optional. The Indicator Applet Complete (or equivalent) must be present in the MATE panel for the top-bar indicator to appear.

### Deployment outline — advanced users only

1. **Back up your current working fan service**, Python daemon, and `fan*_min` readings.
2. Review the source; replace the sample user path in `systemd/imac-odd-fan.service` and the desktop file. Verify the fan labels and curves against **your** hardware.
3. Ensure exactly **one** fan-control daemon is active; do not run two programs that write `fan1_output` / `fan*_min` simultaneously.
4. Test interactively with `sensors` and `journalctl -u imac-odd-fan.service -f`. Confirm automatic mode remains `0` for HDD and CPU.
5. Only after repeated safe tests enable the systemd service. Set the `IMAC_FAN_CURVES` environment variable to the GUI configuration file if using user-specific sliders.
6. Install GUI and panel Python files under `~/.local/bin/` and use the MATE launcher/autostart template; remove old duplicate autostarts.

The GUI configuration file is `~/.config/imac-fan-curves.json` with keys `ODD`, `HDD`, `CPU` and values 0–100. **The exported daemon currently hard-codes `/home/imac/.config/imac-fan-curves.json`; adapt it deliberately and verify file permissions when using a different username.**

### Emergency rollback

If the daemon's behavior is abnormal, **prioritize cooling over noise**. Stop the test, leave the ODD fan at a high protective RPM (the daemon's shutdown handler requests maximum), and restore the original known-good controller/configuration. Restoring the HDD/CPU factory minimums must only happen after confirming the fan modes and hardware match your machine. See [`../docs/thermal-safety.md`](../docs/thermal-safety.md).

## Limitations

This software cannot physically restore a disconnected ODD temperature sensor. Software-based proxy cooling is not equivalent to a factory thermal system. We have not validated it across other iMac revisions, SSD placements, ambient conditions, or prolonged stress tests.

On the owner's machine, the Radeon HD 4850 internal-display workaround is documented separately in [Radeon HD 4850 Optimization](../radeon-hd4850/README.md). The fan tool does not patch the Radeon kernel driver.

## Status

**Exact source snapshot / experimental outside the reference iMac.** The owner reports a functioning cooling daemon and desktop UI. The four uploaded scripts were verified against the exported ZIP using Git blob hashes; the actual systemd unit and boot configuration were not included in that export. Independent hardware validation and further code review are still pending.

Licensed under [GPL-2.0-only](../LICENSE); third-party icons, fonts, and themes are **not included**.
