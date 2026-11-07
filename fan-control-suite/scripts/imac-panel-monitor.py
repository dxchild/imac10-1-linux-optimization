#!/usr/bin/env python3
"""iMac top-panel temperature status indicator (non-privileged)."""
from pathlib import Path
import subprocess
import sys
import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AppIndicator
from gi.repository import GLib, Gtk

BASE = next(iter(Path("/sys/devices/platform").glob("applesmc.*")), None)

def sample():
    vals = {}
    if BASE is None:
        return vals
    for label in BASE.glob("temp*_label"):
        try:
            code = label.read_text().strip()
            p = label.with_name(label.name.replace("_label", "_input"))
            value = float(p.read_text()) / 1000
            if 15 <= value <= 110:
                vals[code] = value
        except (OSError, ValueError):
            pass
    return vals

def maximum(vals, keys):
    found = [vals[x] for x in keys if x in vals]
    return max(found) if found else None

def rpm(n):
    try:
        return f"{int((BASE / f'fan{n}_input').read_text())} RPM"
    except (OSError, ValueError, TypeError):
        return "N/A"

class Monitor:
    def __init__(self):
        self.indicator = AppIndicator.Indicator.new(
            "imac-fan-control",
            "utilities-system-monitor",
            AppIndicator.IndicatorCategory.HARDWARE
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title("iMac Fan Control")
        menu = Gtk.Menu()
        self.items = {}
        for key in ("GPU","Chipset","PSU","CPU heatsink","ODD","HDD","CPU fan"):
            row = Gtk.MenuItem(label="Reading...")
            row.set_sensitive(False)
            menu.append(row)
            self.items[key] = row
        menu.append(Gtk.SeparatorMenuItem())
        launch = Gtk.MenuItem(label="Open iMac Fan Control")
        launch.connect("activate", self.open_main)
        menu.append(launch)
        quit_item = Gtk.MenuItem(label="Quit temperature indicator")
        quit_item.connect("activate", lambda *_: Gtk.main_quit())
        menu.append(quit_item)
        menu.show_all()
        self.indicator.set_menu(menu)
        self.refresh()
        GLib.timeout_add_seconds(5, self.refresh)

    def open_main(self, *_):
        # Launcher is responsible for avoiding duplicate windows.
        launcher = Path.home() / ".local/bin/imac-fan-suite.sh"
        if launcher.exists():
            subprocess.Popen(["/bin/bash",str(launcher)],
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["/usr/bin/python3",
                str(Path.home()/".local/bin/imac-fan-control.py")])

    def refresh(self):
        vals = sample()
        gpu = maximum(vals, ("TG0D","TG0H","TG0P"))
        if gpu is not None:
            self.indicator.set_label(f"GPU {gpu:.0f}°C","GPU 888°C")
        else:
            self.indicator.set_label("GPU N/A","GPU 888°C")
        entries = {
            "GPU": gpu,
            "Chipset": vals.get("TN0H"),
            "PSU": vals.get("Tp2H"),
            "CPU heatsink": vals.get("TC0H"),
        }
        for key,value in entries.items():
            self.items[key].set_label(
                f"{key}: {value:.1f} °C" if value is not None else f"{key}: N/A")
        for name,n in (("ODD",1),("HDD",2),("CPU fan",3)):
            self.items[name].set_label(f"{name}: {rpm(n)}")
        return True

if __name__ == "__main__":
    Monitor()
    Gtk.main()
