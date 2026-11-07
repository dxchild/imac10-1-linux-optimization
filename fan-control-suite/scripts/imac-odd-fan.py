#!/usr/bin/env python3
import json
import os
import signal
import sys
import time
from pathlib import Path

smcs = list(Path('/sys/devices/platform').glob('applesmc.*'))
if not smcs:
    sys.exit('Apple SMC not found')

smc = smcs[0]
config = Path('/home/imac/.config/imac-fan-curves.json')
running = True

# Existing ODD protection: never reduce these thresholds.
old_curves = {
    'GPU': [
        (55, 1200), (60, 1500), (65, 1800),
        (70, 2200), (75, 2700), (80, 3300)
    ],
    'Chipset': [
        (55, 1200), (60, 1350), (65, 1500),
        (70, 1900), (75, 2400), (80, 3000)
    ],
    'PSU': [
        (50, 1200), (55, 1400), (60, 1600),
        (65, 1900), (70, 2400), (75, 3000)
    ]
}

def read(name):
    return int((smc / name).read_text())

def write(name, value):
    (smc / name).write_text(str(int(value)) + '\n')

def temperatures():
    values = {}

    for p in smc.glob('temp*_label'):
        try:
            name = p.read_text().strip()
            path = p.with_name(
                p.name.replace('_label', '_input')
            )
            temp = float(path.read_text()) / 1000

            if 15 <= temp <= 110:
                values[name] = temp
        except (OSError, ValueError):
            pass

    # Additional CPU core sensors
    for hw in Path('/sys/class/hwmon').glob('hwmon*'):
        try:
            if (hw / 'name').read_text().strip() != 'coretemp':
                continue

            for p in hw.glob('temp*_input'):
                temp = float(p.read_text()) / 1000
                if 15 <= temp <= 110:
                    values['CORE_' + p.stem] = temp
        except (OSError, ValueError):
            pass

    return values

def hottest(values, names):
    found = [values[n] for n in names if n in values]
    return max(found) if found else None

def settings():
    try:
        data = json.loads(config.read_text())
        return {
            name: max(0, min(100, int(data.get(name, 0))))
            for name in ('ODD', 'HDD', 'CPU')
        }
    except (OSError, ValueError, TypeError, AttributeError):
        return {'ODD': 0, 'HDD': 0, 'CPU': 0}

def response(temp, start, end, minimum, maximum, boost):
    if temp is None:
        return minimum

    # 0% = original fan control (no boost)
    p = max(0.0, min(1.0, (temp-start)/(end-start)))

    # A higher boost can only increase the response.
    strength = boost / 100.0
    p = p * strength

    return round(minimum + p*(maximum-minimum))

def old_protection(name, temp, maximum):
    if temp is None:
        return maximum

    for limit, rpm in old_curves[name]:
        if temp < limit:
            return rpm

    return maximum

def stop(*args):
    global running
    running = False

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

# Original factory minimum speeds measured on this iMac
minimum = {
    1: read('fan1_min'),
    2: 1100,
    3: 940
}

maximum = {
    n: read(f'fan{n}_max')
    for n in (1, 2, 3)
}

# HDD and CPU must remain in firmware automatic mode.
for n in (2, 3):
    if read(f'fan{n}_manual') != 0:
        sys.exit(f'Fan {n} is not automatic. Aborting.')

try:
    previous = None

    while running:
        t = temperatures()
        levels = settings()

        gpu = hottest(t, ('TG0D', 'TG0H', 'TG0P'))
        chip = t.get('TN0H')
        psu = t.get('Tp2H')
        board = hottest(t, ('Tm0P', 'TM0P'))

        cpu_values = [
            t[k] for k in ('TC0D', 'TC0P', 'TC0H')
            if k in t
        ]
        cpu_values += [
            v for k, v in t.items()
            if k.startswith('CORE_')
        ]
        cpu = max(cpu_values) if cpu_values else None

        # ODD: three sensor regions + previous protection
        if gpu is None or chip is None or psu is None:
            odd_rpm = maximum[1]
        else:
            effective = max(gpu, chip-5, psu)

            odd_rpm = max(
                response(
                    effective, 45, 80,
                    max(1200, minimum[1]),
                    maximum[1], levels['ODD']
                ),
                old_protection('GPU', gpu, maximum[1]),
                old_protection('Chipset', chip, maximum[1]),
                old_protection('PSU', psu, maximum[1])
            )

        # HDD: raised minimum, firmware automatic remains active
        chassis = [
            v for v in (gpu, chip, psu, board)
            if v is not None
        ]
        hdd_temp = max(chassis) if chassis else None

        hdd_rpm = response(
            hdd_temp, 55, 90,
            minimum[2], maximum[2], levels['HDD']
        )

        # CPU: raised minimum, firmware automatic remains active
        cpu_rpm = response(
            cpu, 55, 90,
            minimum[3], maximum[3], levels['CPU']
        )

        targets = {
            1: max(minimum[1], min(maximum[1], odd_rpm)),
            2: max(minimum[2], min(maximum[2], hdd_rpm)),
            3: max(minimum[3], min(maximum[3], cpu_rpm))
        }

        if read('fan1_manual') != 1:
            write('fan1_manual', 1)

        write('fan1_output', targets[1])

        for n in (2, 3):
            try:
                if read(f'fan{n}_min') != targets[n]:
                    write(f'fan{n}_min', targets[n])
            except OSError as error:
                print(f'Fan {n} boost failed: {error}', flush=True)

        state = tuple(targets.values()) + tuple(levels.values())

        if state != previous:
            print(
                f'GPU={gpu} CHIP={chip} PSU={psu} CPU={cpu} | '
                f'ODD={targets[1]} HDD minimum={targets[2]} '
                f'CPU minimum={targets[3]} | Boost={levels}',
                flush=True
            )
            previous = state

        for _ in range(10):
            if not running:
                break
            time.sleep(0.5)

finally:
    # Restore HDD and CPU original minimums.
    for n in (2, 3):
        try:
            write(f'fan{n}_min', minimum[n])
        except OSError:
            pass

    # Missing ODD sensor: leave it at maximum for safety.
    try:
        write('fan1_manual', 1)
        write('fan1_output', maximum[1])
    except OSError:
        pass
