#!/usr/bin/python3
from pathlib import Path
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')

from gi.repository import Gtk, GLib
from gi.repository import AyatanaAppIndicator3 as Indicator

SMC = next(
    iter(Path('/sys/devices/platform').glob('applesmc.*')),
    None
)

def read_temps():
    result = {}
    if SMC is None:
        return result

    for p in SMC.glob('temp*_label'):
        try:
            name = p.read_text().strip()
            inp = p.with_name(
                p.name.replace('_label', '_input')
            )
            temp = float(inp.read_text()) / 1000

            if 15 <= temp <= 110:
                result[name] = temp
        except (ValueError, OSError):
            pass

    return result

def rpm(index):
    if SMC is None:
        return 'N/A'
    try:
        value = int(
            (SMC / f'fan{index}_input').read_text()
        )
        return f'{value} RPM'
    except (ValueError, OSError):
        return 'N/A'

def show_temp(value):
    return f'{value:.1f} °C' if value is not None else 'N/A'

def hottest(data, codes):
    values = [data[k] for k in codes if k in data]
    return max(values) if values else None

class PanelMonitor:
    def __init__(self):
        self.ind = Indicator.Indicator.new(
            'imac-temperature-monitor',
            'utilities-system-monitor',
            Indicator.IndicatorCategory.HARDWARE
        )

        self.menu = Gtk.Menu()
        self.items = {}

        for key in (
            'gpu', 'chipset', 'psu', 'cpu',
            'odd', 'hdd', 'cpu_fan'
        ):
            item = Gtk.MenuItem(label='Betöltés...')
            item.set_sensitive(False)
            self.items[key] = item
            self.menu.append(item)

        self.menu.append(Gtk.SeparatorMenuItem())

        gui = Path.home() / '.local/bin/imac-fan-control.py'

        if gui.is_file():
            entry = Gtk.MenuItem(
                label='Fan Control megnyitása'
            )
            entry.connect(
                'activate',
                lambda *_: subprocess.Popen(
                    ['/usr/bin/python3', str(gui)]
                )
            )
            self.menu.append(entry)

        exit_item = Gtk.MenuItem(
            label='Panelkijelző bezárása'
        )
        exit_item.connect(
            'activate',
            lambda *_: Gtk.main_quit()
        )
        self.menu.append(exit_item)

        self.menu.show_all()
        self.ind.set_menu(self.menu)
        self.ind.set_status(
            Indicator.IndicatorStatus.ACTIVE
        )

        self.refresh()
        GLib.timeout_add_seconds(5, self.refresh)

    def refresh(self):
        t = read_temps()

        gpu = hottest(
            t, ('TG0D', 'TG0H', 'TG0P')
        )
        chipset = t.get('TN0H')
        psu = t.get('Tp2H')
        cpu = t.get('TC0H')

        label = (
            f'GPU {gpu:.0f}°C'
            if gpu is not None else 'GPU N/A'
        )

        self.ind.set_label(label, 'GPU 888°C')

        data = {
            'gpu': f'GPU: {show_temp(gpu)}',
            'chipset': f'Chipset: {show_temp(chipset)}',
            'psu': f'Tápegység: {show_temp(psu)}',
            'cpu': f'CPU hűtőborda: {show_temp(cpu)}',
            'odd': f'ODD ventilátor: {rpm(1)}',
            'hdd': f'HDD ventilátor: {rpm(2)}',
            'cpu_fan': f'CPU ventilátor: {rpm(3)}'
        }

        for key, value in data.items():
            self.items[key].set_label(value)

        return True

if __name__ == '__main__':
    PanelMonitor()
    Gtk.main()
