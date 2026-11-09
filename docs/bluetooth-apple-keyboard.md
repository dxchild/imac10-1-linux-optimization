# Bluetooth & Apple Wireless Keyboard — iMac10,1 (2009)

[Magyar útmutató](bluetooth-apple-keyboard.hu.md) · [Project homepage](../README.md)

## Status (November 9, 2026)

**Observed on one iMac10,1 running Ubuntu MATE 24.04 (Linux 6.8.0-147-generic).**

- The original built-in Apple Bluetooth adapter is detected: USB ID `05ac:8215`, Bluetooth **2.0 + EDR**.
- Linux loads `btusb` and the Bluetooth service has a powered, unblocked controller; `bluetoothctl` was able to discover a device.
- The bundled Blueman **2.3.5-3build1** repeatedly generated crash reports for `/usr/bin/blueman-applet`, reporting `gi.repository.GLib.GError` in `call_finish` (D-Bus activity). The complete underlying D-Bus error was not captured in the published screenshots.
- The owner built/installed **Blueman 2.4.3-1** from Debian packaging and verified the installed package version using `dpkg-query`.
- The Apple Wireless Keyboard was paired and produced keystrokes. However, characters were wrong for some letter keys, matching an embedded numeric keypad / Num Lock issue. **The persistence of the Num Lock fix has not yet been independently confirmed.**
- A later reboot test is still required to confirm that Blueman 2.4.3 no longer crashes. **Do not claim this as a universally verified fix for Ubuntu MATE 24.04.**

The Bluetooth and the keyboard issues are distinct. Upgrading Blueman does **not** upgrade the built-in Bluetooth radio, which lacks Bluetooth Low Energy (BLE) support.

## Read-only hardware checks

Run these in a **regular shell**, where the prompt resembles `user@host:~$`, not inside the interactive `[bluetooth]#` prompt.

```bash
uname -r
lsusb | grep -Ei 'bluetooth|broadcom|apple'
systemctl is-active bluetooth
bluetoothctl list
bluetoothctl show
rfkill list
lsmod | grep -E 'btusb|btbcm|bluetooth'
journalctl -k -b --no-pager | grep -Ei 'bluetooth|btusb|hci0|firmware' | tail -n 30
```

A controller displayed with `Powered: yes` and no rfkill blocks suggests the radio is recognized. This alone does **not** verify successful pairing or data transfer.

To scan for nearby **pairable** classic Bluetooth equipment:

```bash
bluetoothctl
power on
agent on
default-agent
scan on
# Put the other device in pairing mode; watch for [NEW] Device.
devices
scan off
quit
```

Once `quit` returns you to your normal shell, graphical apps and `apt` commands will work again.

## Blueman crash and tested package version

The original Ubuntu 24.04 package was `2.3.5-3build1`. Its crash report showed `ExecutablePath: /usr/bin/blueman-applet`, `ProblemType: Crash`, and a traceback through `gi.repository.GLib.GError` / `call_finish`. The report also listed an outdated `libsqlite3-0`, but that does **not** prove SQLite caused the Blueman crash.

The Ubuntu 24.04 apt repositories on this iMac did not offer a newer Blueman candidate. The owner's final result:

```console
$ dpkg-query -W -f='${Version}\n' blueman
2.4.3-1
```

The Debian `2.4.3-1` source package was used to build a local `.deb` in `~/blueman-build`. The reported development workflow was:

```bash
# Example for experienced builders — NOT an unattended installer.
sudo apt update
sudo apt install git build-essential dpkg-dev debhelper dh-python fakeroot \
    python3-dev python-gi-dev cython3 libbluetooth-dev \
    libpolkit-agent-1-dev libglib2.0-dev \
    libgirepository-1.0-dev libcairo2-dev gettext \
    meson ninja-build pkg-config

mkdir -p ~/blueman-build
cd ~/blueman-build
git clone --depth 1 --branch debian/2.4.3-1 \
    https://salsa.debian.org/debian/blueman.git
cd blueman
dpkg-buildpackage -us -uc -b -j2
ls -lh ../*.deb

# Before installing a cross-distribution package, inspect the apt simulation:
sudo apt -s install ../blueman_2.4.3-1_amd64.deb
# Install ONLY if no unintended removals/dependency changes are proposed.
# sudo apt install ../blueman_2.4.3-1_amd64.deb
```

**Caution:** a Debian-built package on Ubuntu is a cross-distribution override and may not receive routine Ubuntu security/bug-fix updates. Review installed files and dependency changes; keep rollback media and the Ubuntu package version available. Build dependencies can differ from this example, depending on the source tree and local apt state.

Re-check the installed version:

```bash
dpkg-query -W -f='${Version}\n' blueman
apt-cache policy blueman
```

## Keyboard types numbers instead of letters

After pairing the Apple keyboard, pressing letters produced unexpected digits. This is consistent with **Num Lock enabling the keyboard's embedded numeric keypad** on some older compact Apple keyboards. The exact model and key mapping have not been independently verified.

Try the keyboard's Num Lock/Fn shortcut (it may be `Fn+F6` on some Apple models). On an X11 MATE session, `numlockx` can also be tested:

```bash
sudo apt install numlockx
numlockx off
```

Test the alphabetic keys again. If **and only if** that fixes the issue, consider a per-user MATE autostart entry for `numlockx off`; the long-term result on this specific setup is still **unverified**. If the problem is merely the keyboard layout (Hungarian vs US), change the XKB layout instead — Num Lock is not a universal explanation for wrong characters.

## Remaining checks

- [x] Bluetooth USB controller recognized and powered
- [x] Device discovery observed from `bluetoothctl`
- [x] Blueman 2.4.3-1 package installation verified
- [x] Apple Bluetooth keyboard paired and sends input
- [ ] Confirm Blueman no longer crashes after multiple logins
- [ ] Confirm keyboard typing and Num Lock behavior after reboot
- [ ] Check additional Bluetooth Classic devices and profiles

## Notes

No personal Bluetooth MAC addresses are included in this documentation. This is one hardware/software case study, not a guarantee that the same package or keyboard shortcut applies to every iMac10,1 or Apple Wireless Keyboard.

Further work on the GPU and cooling is in [Radeon HD 4850](../radeon-hd4850/README.md) and [Fan Control Suite](../fan-control-suite/README.md).
