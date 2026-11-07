#!/usr/bin/env python3
"""iMac10,1 Apple SMC cooling engine (community reconstruction).

ODD: sensor-driven manual control. HDD/CPU: keep firmware automatic
and raise the minimum RPM only, never below measured factory floors.
Root-only sysfs access. Change your machine's fans at your own risk.
"""
import json
import signal
import sys
import time
from pathlib import Path

CONFIG = Path("/etc/imac-fan-control/curves.json")
# Override only if running a service configured for the user's login:
# Environment=IMAC_FAN_CURVES=/home/YOUR_USER/.config/imac-fan-curves.json
import os
if os.environ.get("IMAC_FAN_CURVES"):
    CONFIG = Path(os.environ["IMAC_FAN_CURVES"])

FLOORS = {1: 900, 2: 1100, 3: 940}  # measured on a specific iMac10,1
EXPECTED = {1: "ODD", 2: "HDD", 3: "CPU"}
SENSORS = {
    "GPU": ("TG0D", "TG0H", "TG0P"),
    "Chipset": ("TN0H",),
    "PSU": ("Tp2H",),
}
BASE_CURVES = {
    "GPU": [(55, 1200), (60, 1500), (65, 1800), (70, 2200),
            (75, 2700), (80, 3300)],
    "Chipset": [(55, 1200), (60, 1350), (65, 1500), (70, 1900),
                (75, 2400), (80, 3000)],
    "PSU": [(50, 1200), (55, 1400), (60, 1600), (65, 1900),
            (70, 2400), (75, 3000)],
}
stop = False

def stopping(*_):
    global stop
    stop = True

def smc_root():
    matches = list(Path("/sys/devices/platform").glob("applesmc.*"))
    if len(matches) != 1:
        raise RuntimeError("Expected one applesmc platform device")
    base = matches[0]
    actual = {n: (base / f"fan{n}_label").read_text().strip().upper()
              for n in EXPECTED}
    if any(EXPECTED[n] not in actual[n] for n in EXPECTED):
        raise RuntimeError(f"Unexpected fan labels: {actual}")
    for n in EXPECTED:
        if int((base / f"fan{n}_min").read_text()) < 0:
            raise RuntimeError("Invalid SMC fan minimum")
    return base

def read_int(root, name):
    return int((root / name).read_text())

def write_int(root, name, value):
    (root / name).write_text(str(int(value)) + "\n")

def temperatures(root):
    values = {}
    for label in root.glob("temp*_label"):
        try:
            code = label.read_text().strip()
            reading = label.with_name(label.name.replace("_label", "_input"))
            v = float(reading.read_text()) / 1000.0
            if 15 <= v <= 110:
                values[code] = v
        except (OSError, ValueError):
            pass
    for hw in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            if (hw / "name").read_text().strip() != "coretemp":
                continue
            for p in hw.glob("temp*_input"):
                v = float(p.read_text()) / 1000.0
                if 15 <= v <= 110:
                    values["CORE_" + p.stem] = v
        except (OSError, ValueError):
            pass
    return values

def hottest(data, keys):
    found = [data[k] for k in keys if k in data]
    return max(found) if found else None

def configuration():
    try:
        values = json.loads(CONFIG.read_text())
        return {key: max(0, min(100, int(values.get(key, 0))))
                for key in ("ODD", "HDD", "CPU")}
    except (OSError, TypeError, ValueError, AttributeError):
        return {"ODD": 0, "HDD": 0, "CPU": 0}

def stepped(temp, curve, maximum):
    if temp is None:
        return maximum  # missing sensor means fail safe
    for threshold, rpm in curve:
        if temp < threshold:
            return rpm
    return maximum

def boost(temp, begin, end, floor, maximum, percent):
    # At 0% the requested floor remains exactly the original baseline.
    if temp is None or percent <= 0:
        return floor
    fraction = max(0.0, min(1.0, (temp - begin) / (end - begin)))
    return round(floor + fraction * percent / 100.0 * (maximum - floor))

def run():
    root = smc_root()
    maximum = {n: read_int(root, f"fan{n}_max") for n in EXPECTED}
    if any(maximum[n] <= FLOORS[n] for n in EXPECTED):
        raise RuntimeError("Incompatible fan RPM range")
    if any(read_int(root, f"fan{n}_manual") != 0 for n in (2, 3)):
        raise RuntimeError("HDD or CPU is already manually controlled")
    # We observed these baselines on THIS machine; verify before copying.
    print("iMac SMC fan control started", flush=True)
    last = None
    try:
        while not stop:
            t = temperatures(root)
            settings = configuration()
            temps = {name: hottest(t, codes) for name, codes in SENSORS.items()}
            if any(v is None for v in temps.values()):
                odd = maximum[1]
            else:
                baseline = max(stepped(temps[name], BASE_CURVES[name], maximum[1])
                               for name in SENSORS)
                equivalent = max(temps["GPU"], temps["Chipset"] - 5, temps["PSU"])
                odd = max(baseline, boost(equivalent, 45, 80, 1200,
                                          maximum[1], settings["ODD"]))
            chassis = [temps[k] for k in ("GPU", "Chipset", "PSU")
                       if temps[k] is not None]
            board = hottest(t, ("Tm0P", "TM0P"))
            if board is not None:
                chassis.append(board)
            hdd = max(chassis) if chassis else None
            core = [v for k, v in t.items() if k.startswith("CORE_")]
            cpu = [v for v in (hottest(t, ("TC0D", "TC0P", "TC0H")), *core)
                   if v is not None]
            cpu = max(cpu) if cpu else None
            targets = {
                1: max(FLOORS[1], min(maximum[1], odd)),
                2: boost(hdd, 55, 90, FLOORS[2], maximum[2], settings["HDD"]),
                3: boost(cpu, 55, 90, FLOORS[3], maximum[3], settings["CPU"]),
            }
            if read_int(root, "fan1_manual") != 1:
                write_int(root, "fan1_manual", 1)
            write_int(root, "fan1_output", targets[1])
            for n in (2, 3):
                if read_int(root, f"fan{n}_manual") != 0:
                    raise RuntimeError(f"Fan {n} switched out of automatic mode")
                if read_int(root, f"fan{n}_min") != targets[n]:
                    write_int(root, f"fan{n}_min", targets[n])
            snapshot = (tuple(targets.values()), tuple(settings.values()))
            if snapshot != last:
                print(f"temp={temps} target_rpm={targets} boost={settings}", flush=True)
                last = snapshot
            for _ in range(10):
                if stop:
                    break
                time.sleep(0.5)
    finally:
        # No missing-ODD-sensor protection after daemon exits.
        # Request full ODD fan RPM in that failure mode.
        try:
            write_int(root, "fan1_manual", 1)
            write_int(root, "fan1_output", maximum[1])
        except OSError:
            pass
        for n in (2, 3):
            try:
                write_int(root, f"fan{n}_min", FLOORS[n])
            except OSError:
                pass

if __name__ == "__main__":
    signal.signal(signal.SIGINT, stopping)
    signal.signal(signal.SIGTERM, stopping)
    try:
        run()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAN CONTROL ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
