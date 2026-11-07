# Thermal safety and recovery

> **WARNING:** Direct writes to `/sys/devices/platform/applesmc.*/fan*_manual`, `fan*_output`, or `fan*_min` can cause insufficient cooling, excess noise, or hardware damage. These examples were developed for one modified iMac10,1. Review the code before running as root.

## Never assume fan order

The reference machine reported fan1 = ODD, fan2 = HDD, fan3 = CPU. Confirm your own `fan*_label`, `fan*_min`, `fan*_max`, `fan*_manual` and `fan*_input` values. Do not rely on the labels from someone else's iMac.

## The base safety rules

1. The ODD fan is controlled by software **only because its original temperature feedback is unreliable on the modified test machine**.
2. Missing GPU/chipset/PSU sensor data must cause higher protective ODD cooling, never silently reduce cooling.
3. HDD and CPU `fan*_manual` must remain `0` (firmware automatic). The control service may raise their minimum RPM only on compatible hardware.
4. A GUI boost of `0` means no extra speed beyond the previous thermal baseline or factory automatic control. It does *not* imply a constant 900 RPM ODD setting.
5. Watch the actual fan RPMs and temperatures when testing. The displayed model target is not proof of the fan reaching that RPM.
6. If the sensor wiring or fans differ, **do not enable** this daemon until the code is adapted and verified.

## Inspect without writing

```bash
sensors
systemctl status imac-odd-fan.service --no-pager
journalctl -u imac-odd-fan.service -n 50 --no-pager
for f in /sys/devices/platform/applesmc.*/fan{1,2,3}_{label,min,max,input,manual}; do
    echo "$f: $(cat "$f")"
done
```

## Prepare a recovery path

Keep a copy of your known-good controller, a way to enter a text console, and a bootable USB. Before modifying anything, save the actual original minimums and manual flags as text:

```bash
for f in /sys/devices/platform/applesmc.*/fan{1,2,3}_{label,min,max,input,manual}; do
    echo "$f: $(cat "$f")"
done > "$HOME/imac-fans-before.txt"
```

The sample daemon's SIGTERM handler requests maximum ODD cooling if it exits and attempts to restore measured HDD and CPU minimums. **An unhandled crash, process kill, power loss, write failure or mismatched hardware can invalidate assumptions about this cleanup behavior.** Do not rely on process-exit cleanup as a substitute for a functioning physical ODD sensor.

If you suspect overheating, immediately stop the risky test and restore the verified known-good setup. Do not force a low fixed RPM to make the iMac quieter. Physical thermal-sensor repair/installation is preferable when available.

## Published source status

As of 2026-11-07, the four `fan-control-suite/scripts/` files are an exact export from the owner's working iMac ZIP archive (Git blob checksums verified). The systemd unit and desktop autostart templates were not part of the export. This does **not** certify the daemon for other hardware: it relies on fixed iMac10,1 fan mappings, 1100/940 RPM HDD/CPU floors and `/home/imac` for the curve file. Do not automatically replace a working installed service or run two fan-writing programs. Review and test before any deployment.
