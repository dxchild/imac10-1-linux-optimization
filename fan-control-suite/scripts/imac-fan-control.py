# IMAC_LAYOUT_V5
#!/usr/bin/env python3

import json
import os
import subprocess
import tkinter as tk
from collections import deque
from pathlib import Path

# ---------------- STYLE ----------------
APP_W = 1000
APP_H = 940

BG = '#111214'
HEADER = '#17181b'
CARD = '#1d1f23'
BORDER = '#2b2d31'
TEXT = '#f5f5f7'
MUTED = '#a1a1aa'
GRID = '#3a3c41'
TRACK = '#4b4d53'
SUBTLE = '#d1d1d6'

BLUE = '#0A84FF'
GREEN = '#30D158'
PURPLE = '#BF5AF2'
YELLOW = '#FFD60A'
ORANGE = '#FF9F0A'
WHITE = '#FFFFFF'

FONT = 'Inter'

# ---------------- SMC / CONFIG ----------------
SMC = next(iter(Path('/sys/devices/platform').glob('applesmc.*')), None)
CONFIG = Path.home() / '.config/imac-fan-curves.json'

FAN_NUM = {'ODD': 1, 'HDD': 2, 'CPU': 3}
FAN_COLOR = {'ODD': BLUE, 'HDD': GREEN, 'CPU': PURPLE}
TEMP_HISTORY = {
    'GPU': deque(maxlen=120),
    'CHIPSET': deque(maxlen=120),
    'POWER SUPPLY': deque(maxlen=120)
}

SLIDER_RECTS = {}
RESET_RECT = None
dragging = None
pending_save = None
redraw_pending = False

# ---------------- ROOT ----------------
root = tk.Tk()
root.title('iMac Fan Control')
root.geometry(f'{APP_W}x{APP_H}')
root.resizable(False, False)
root.configure(bg=BG)

canvas = tk.Canvas(root, width=APP_W, height=APP_H, bg=BG, highlightthickness=0)
canvas.pack(fill='both', expand=True)

# ---------------- HELPERS ----------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def fclamp(v):
    return max(0.0, min(1.0, v))

def read_int(name):
    if SMC is None:
        return None
    try:
        return int((SMC / name).read_text().strip())
    except (OSError, ValueError):
        return None

def read_temps():
    out = {}

    if SMC is not None:
        for p in SMC.glob('temp*_label'):
            try:
                label = p.read_text().strip()
                inp = p.with_name(p.name.replace('_label', '_input'))
                val = float(inp.read_text()) / 1000.0
                if 15 <= val <= 110:
                    out[label] = val
            except (OSError, ValueError):
                pass

    for hw in Path('/sys/class/hwmon').glob('hwmon*'):
        try:
            if (hw / 'name').read_text().strip() != 'coretemp':
                continue
        except OSError:
            continue

        for p in hw.glob('temp*_input'):
            try:
                val = float(p.read_text()) / 1000.0
                if 15 <= val <= 110:
                    out[f'CORE_{p.stem}'] = val
            except (OSError, ValueError):
                pass

    return out

def maxof(data, names):
    vals = [data[n] for n in names if n in data]
    return max(vals) if vals else None

def get_levels():
    try:
        data = json.loads(CONFIG.read_text())
        return {
            name: clamp(int(data.get(name, 0)), 0, 100)
            for name in FAN_NUM
        }
    except Exception:
        return {'ODD': 0, 'HDD': 0, 'CPU': 0}

def write_levels():
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG.with_suffix('.json.tmp')
        tmp.write_text(json.dumps({
            name: levels[name].get()
            for name in levels
        }, indent=2) + '\n')
        os.replace(tmp, CONFIG)
    except OSError as e:
        print('Save error:', e)

def service_active():
    try:
        r = subprocess.run(
            ['systemctl', 'is-active', 'imac-odd-fan.service'],
            capture_output=True, text=True, timeout=1
        )
        return r.stdout.strip() == 'active'
    except Exception:
        return None

def rounded_rect(x, y, w, h, fill=CARD, outline=BORDER, radius=18, width=1):
    x2, y2 = x + w, y + h
    r = min(radius, w/2, h/2)

    points = [
        x+r, y,
        x2-r, y,
        x2, y,
        x2, y+r,
        x2, y2-r,
        x2, y2,
        x2-r, y2,
        x+r, y2,
        x, y2,
        x, y2-r,
        x, y+r,
        x, y
    ]

    canvas.create_polygon(
        points,
        smooth=True,
        splinesteps=20,
        fill=fill,
        outline=outline,
        width=width
    )

def txt(x, y, text, size=12, color=TEXT, weight='normal', anchor='nw'):
    canvas.create_text(
        x, y,
        text=text,
        fill=color,
        anchor=anchor,
        font=(FONT, size, weight)
    )

def nice_temp(v):
    return f'{v:.1f} °C' if v is not None else 'N/A'

def nice_rpm(v):
    return f'{v} RPM' if v is not None else 'N/A'

def draw_progress(x, y, w, frac, color):
    rounded_rect(x, y, w, 7, fill=TRACK, outline=TRACK, radius=4, width=1)
    frac = fclamp(frac)
    if frac > 0:
        filled = max(7, w * frac)
        rounded_rect(x, y, filled, 7, fill=color, outline=color, radius=4, width=1)

# ---------------- THERMAL MODEL ----------------
def odd_source_temp(data):
    gpu = maxof(data, ('TG0D', 'TG0H', 'TG0P'))
    chip = data.get('TN0H')
    psu = data.get('Tp2H')
    if gpu is None or chip is None or psu is None:
        return None
    return max(gpu, chip - 5, psu)

def hdd_source_temp(data):
    vals = [
        maxof(data, ('TG0D', 'TG0H', 'TG0P')),
        data.get('TN0H'),
        data.get('Tp2H'),
        maxof(data, ('Tm0P', 'TM0P'))
    ]
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None

def cpu_source_temp(data):
    vals = [
        data.get('TC0H'),
        data.get('TC0P'),
        data.get('TC0D')
    ]
    vals += [v for k, v in data.items() if k.startswith('CORE_')]
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None

def current_fraction(name, data):
    if name == 'ODD':
        t = odd_source_temp(data)
        return 1.0 if t is None else fclamp((t - 45.0) / 35.0)
    if name == 'HDD':
        t = hdd_source_temp(data)
        return 0.0 if t is None else fclamp((t - 55.0) / 35.0)
    t = cpu_source_temp(data)
    return 0.0 if t is None else fclamp((t - 55.0) / 35.0)

def curve_targets(name, fraction, data, level):
    level = clamp(int(level), 0, 100)
    number = FAN_NUM[name]
    max_defaults = {'ODD': 3800, 'HDD': 5500, 'CPU': 4600}
    maximum = read_int(f'fan{number}_max') or max_defaults[name]

    if name == 'HDD':
        minimum = 1100
        baseline = minimum
        selected = round(minimum + fraction * (level/100.0) * (maximum - minimum))
        return baseline, clamp(selected, minimum, maximum), minimum, maximum

    if name == 'CPU':
        minimum = 940
        baseline = minimum
        selected = round(minimum + fraction * (level/100.0) * (maximum - minimum))
        return baseline, clamp(selected, minimum, maximum), minimum, maximum

    minimum = max(1200, read_int('fan1_min') or 900)

    gpu = maxof(data, ('TG0D', 'TG0H', 'TG0P'))
    chip = data.get('TN0H')
    psu = data.get('Tp2H')

    if gpu is None or chip is None or psu is None:
        return maximum, maximum, minimum, maximum

    ref = max(gpu, chip - 5, psu)
    simulated_temp = 45 + 35 * fraction

    curves = {
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

    simulated = {
        'GPU': simulated_temp + gpu - ref,
        'Chipset': simulated_temp + chip - ref,
        'PSU': simulated_temp + psu - ref
    }

    requested = []
    for group, temp in simulated.items():
        speed = maximum
        for limit, rpm in curves[group]:
            if temp < limit:
                speed = rpm
                break
        requested.append(speed)

    baseline = max(requested)
    boost = round(minimum + fraction * (level/100.0) * (maximum - minimum))
    selected = max(baseline, boost)

    return baseline, clamp(selected, minimum, maximum), minimum, maximum

# ---------------- DRAWING ----------------
def draw_temp_card(x, y, title, value, dot_color):
    rounded_rect(x, y, 220, 118, fill=CARD, outline=BORDER, radius=18)
    canvas.create_oval(x+18, y+18, x+28, y+28, fill=dot_color, outline='')
    txt(x+38, y+16, title, 11, MUTED, 'bold')
    txt(x+18, y+50, nice_temp(value), 23, TEXT, 'bold')
    txt(x+18, y+92, 'LIVE SENSOR', 10, MUTED)

def draw_fan_card(name, x, y, data):
    color = FAN_COLOR[name]
    number = FAN_NUM[name]

    rounded_rect(
        x, y, 300, 145,
        fill=CARD, outline=BORDER, radius=18
    )

    actual = read_int(f"fan{number}_input")
    level = levels[name].get()
    fraction = current_fraction(name, data)

    _, selected, minimum, maximum = curve_targets(
        name, fraction, data, level
    )

    txt(x+18, y+15, f"{name} FAN", 12, color, "bold")
    txt(x+18, y+45, nice_rpm(actual), 22, TEXT, "bold")

    description = (
        "Modeled target" if name == "ODD"
        else "Requested minimum"
    )

    txt(
        x+18, y+83,
        f"{description}: {selected} RPM",
        10, MUTED
    )

    mode = (
        "Software controlled" if name == "ODD"
        else "Firmware auto + boost"
    )

    txt(x+18, y+107, mode, 10, MUTED)

    fraction = 0
    if actual is not None and maximum > minimum:
        fraction = (
            (actual - minimum) / (maximum - minimum)
        )

    draw_progress(x+18, y+130, 264, fraction, color)


def draw_response_chart(name, x, y, data):
    global SLIDER_RECTS

    color = FAN_COLOR[name]
    level = levels[name].get()

    rounded_rect(x, y, 300, 165, fill=CARD, outline=BORDER, radius=18)

    txt(x+18, y+14, 'Fan Response', 12, TEXT, 'bold')
    txt(x+282, y+14, f'+{level}%', 11, color, 'bold', anchor='ne')

    left = x + 18
    right = x + 282
    top = y + 40
    bottom = y + 92

    for f in (0, 0.5, 1):
        gy = bottom - f * (bottom - top)
        canvas.create_line(left, gy, right, gy, fill=GRID, dash=(2, 5))

    base_points = []
    selected_points = []

    for i in range(81):
        p = i / 80.0
        base, sel, minrpm, maxrpm = curve_targets(name, p, data, level)
        span = max(1, maxrpm - minrpm)
        xx = left + p * (right - left)
        by = bottom - ((base - minrpm) / span) * (bottom - top)
        sy = bottom - ((sel - minrpm) / span) * (bottom - top)
        base_points.extend((xx, by))
        selected_points.extend((xx, sy))

    canvas.create_line(*base_points, fill='#91959d', width=2, dash=(4, 4))
    if name == 'ODD':
        canvas.create_line(*selected_points, fill=color, width=3)
    else:
        canvas.create_line(*selected_points, fill=color, width=3, smooth=True)

    range_label = '45–80 °C' if name == 'ODD' else '55–90 °C'
    txt(x+18, y+103, range_label, 10, MUTED)
    txt(x+282, y+103, 'RPM floor', 10, MUTED, anchor='ne')

    sx1 = x + 18
    sx2 = x + 282
    sy = y + 132

    canvas.create_line(sx1, sy, sx2, sy, fill=TRACK, width=7, capstyle=tk.ROUND)

    handle_x = sx1 + (sx2 - sx1) * (level / 100.0)
    if level > 0:
        canvas.create_line(sx1, sy, handle_x, sy, fill=color, width=7, capstyle=tk.ROUND)

    canvas.create_oval(
        handle_x - 10, sy - 10,
        handle_x + 10, sy + 10,
        fill=WHITE,
        outline='#d6d6db',
        width=1
    )

    txt(x+18, y+144, 'Default', 10, MUTED)
    txt(x+282, y+144, 'Faster', 10, MUTED, anchor='ne')

    SLIDER_RECTS[name] = (sx1, sy-14, sx2, sy+14)

def draw_history_panel(x, y):
    rounded_rect(x, y, 944, 150, fill=CARD, outline=BORDER, radius=18)

def draw_history_graph(x, y):
    left = x + 28
    right = x + 912
    top = y + 24
    bottom = y + 95

    for deg in (40, 60, 80):
        gy = bottom - ((deg - 20) / 80.0) * (bottom - top)
        canvas.create_line(left, gy, right, gy, fill=GRID, dash=(2, 5))
        txt(left - 10, gy, f'{deg}°', 10, MUTED, anchor='e')

    colors = {
        'GPU': BLUE,
        'CHIPSET': YELLOW,
        'POWER SUPPLY': GREEN
    }

    for key, color in colors.items():
        vals = TEMP_HISTORY[key]
        pts = []
        for i, val in enumerate(vals):
            if val is None:
                continue
            xx = left + (i / max(1, len(vals)-1)) * (right - left)
            yy = bottom - ((clamp(val, 20, 100) - 20) / 80.0) * (bottom - top)
            pts.extend((xx, yy))
        if len(pts) >= 4:
            canvas.create_line(*pts, fill=color, width=2, smooth=True)

    lx = x + 34
    for label, color in [('GPU', BLUE), ('CHIPSET', YELLOW), ('POWER SUPPLY', GREEN)]:
        canvas.create_oval(lx, y+116, lx+10, y+126, fill=color, outline='')
        txt(lx+16, y+115, label, 10, MUTED)
        lx += 122 if label != 'POWER SUPPLY' else 160

def draw_reset_button():
    global RESET_RECT

    x, y, w, h = 818, 294, 150, 34
    RESET_RECT = (x, y, x+w, y+h)

    rounded_rect(
        x, y, w, h,
        fill="#2a4563",
        outline="#355373",
        radius=12
    )

    txt(
        x+w/2, y+h/2,
        "Reset to Default",
        10, WHITE, "bold",
        anchor="center"
    )


def draw(capture=True):
    canvas.delete('all')
    SLIDER_RECTS.clear()

    canvas.create_rectangle(0, 0, APP_W, 106, fill=HEADER, outline='')

    txt(28, 18, 'iMac Fan Control', 25, TEXT, 'bold')
    txt(28, 69, 'APPLE SMC / CUSTOM COOLING PROFILE', 11, MUTED, 'normal')

    status = service_active()
    if status is True:
        st_text = '● Cooling Active'
        st_color = GREEN
    elif status is False:
        st_text = '● Service Inactive'
        st_color = ORANGE
    else:
        st_text = '● Status Unknown'
        st_color = ORANGE

    txt(968, 34, st_text, 12, st_color, 'bold', anchor='ne')

    data = read_temps()

    temps_display = {
        'GPU': maxof(data, ('TG0D', 'TG0H', 'TG0P')),
        'CHIPSET': data.get('TN0H'),
        'POWER SUPPLY': data.get('Tp2H'),
        'CPU HEATSINK': data.get('TC0H')
    }

    txt(28, 126, 'Temperatures', 17, TEXT, 'bold')
    draw_temp_card(28, 159, 'GPU', temps_display['GPU'], BLUE)
    draw_temp_card(268, 159, 'CHIPSET', temps_display['CHIPSET'], YELLOW)
    draw_temp_card(508, 159, 'POWER SUPPLY', temps_display['POWER SUPPLY'], GREEN)
    draw_temp_card(748, 159, 'CPU HEATSINK', temps_display['CPU HEATSINK'], PURPLE)

    txt(28, 300, 'Fans & Response Curves', 17, TEXT, 'bold')
    draw_reset_button()

    fan_x = {'ODD': 28, 'HDD': 350, 'CPU': 672}
    for name in ('ODD', 'HDD', 'CPU'):
        draw_fan_card(name, fan_x[name], 348, data)
        draw_response_chart(name, fan_x[name], 506, data)

    txt(28, 693, 'Temperature History', 17, TEXT, 'bold')
    draw_history_panel(28, 726)

    if capture:
        TEMP_HISTORY['GPU'].append(temps_display['GPU'])
        TEMP_HISTORY['CHIPSET'].append(temps_display['CHIPSET'])
        TEMP_HISTORY['POWER SUPPLY'].append(temps_display['POWER SUPPLY'])

    draw_history_graph(28, 726)

    txt(
        28, 905,
        '0% = original cooling  •  sliders only increase fan response  •  temperatures refresh every 2 s',
        10, MUTED
    )

# ---------------- INTERACTION ----------------
initial_levels = get_levels()
levels = {name: tk.IntVar(value=initial_levels[name]) for name in FAN_NUM}

def request_redraw():
    global redraw_pending
    if redraw_pending:
        return
    redraw_pending = True
    root.after(50, perform_redraw)

def perform_redraw():
    global redraw_pending
    redraw_pending = False
    draw(capture=False)

def schedule_save():
    global pending_save
    if pending_save:
        root.after_cancel(pending_save)
    pending_save = root.after(250, write_levels)

def reset_to_default():
    for var in levels.values():
        var.set(0)
    schedule_save()
    request_redraw()

def update_slider(name, mouse_x):
    x1, y1, x2, y2 = SLIDER_RECTS[name]
    frac = fclamp((mouse_x - x1) / max(1, (x2 - x1)))
    step = round((frac * 100) / 5) * 5
    value = clamp(step, 0, 100)
    if levels[name].get() != value:
        levels[name].set(value)
        schedule_save()
        request_redraw()

def on_press(event):
    global dragging

    if RESET_RECT:
        x1, y1, x2, y2 = RESET_RECT
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            reset_to_default()
            return

    dragging = None
    for name, rect in SLIDER_RECTS.items():
        x1, y1, x2, y2 = rect
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            dragging = name
            update_slider(name, event.x)
            return

def on_drag(event):
    if dragging is not None:
        update_slider(dragging, event.x)

def on_release(event):
    global dragging
    dragging = None

canvas.bind('<Button-1>', on_press)
canvas.bind('<B1-Motion>', on_drag)
canvas.bind('<ButtonRelease-1>', on_release)

def refresh():
    draw(capture=True)
    root.after(2000, refresh)

refresh()
root.mainloop()
