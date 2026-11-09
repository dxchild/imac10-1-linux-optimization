# iMac10,1 (2009) — Linux Optimization Project

**Restore graphics, optimize cooling, and document Bluetooth compatibility on a late-2009 Apple iMac running Linux.**

[Magyar leírás](README.hu.md) · [Hardware](docs/hardware.md) · [Thermal safety](docs/thermal-safety.md)

> Community effort on **one tested iMac10,1**. It is not an Apple, Canonical, or upstream Linux release. Hardware changes and kernel modifications are at your own risk.

## Project modules

### 1. Radeon HD 4850 / RV770 — internal display and acceleration

**Tested** on a 27-inch iMac10,1 with internal 2560×1440 display, Ubuntu MATE 24.04 and kernel `6.8.0-147-generic`.

A workaround for an internal-screen black screen and display corruption while enabling the Radeon hardware path instead of relying on `nomodeset` + `llvmpipe`. Includes an upstream commit plus a small, machine-specific follow-up patch. **Not upstream-ready or general-purpose.**

- [Detailed Radeon guide](radeon-hd4850/README.md)
- [Magyar útmutató](radeon-hd4850/README.hu.md)
- [Build script](scripts/build-radeon.sh)
- [Patches](patches/)

The original Radeon `scripts/` and `patches/` paths are intentionally retained so older commands and links remain valid.

### 2. iMac Fan Control Suite — thermal monitoring and three-fan cooling

**Working dashboard and cooling daemon on the owner's SSD-modified iMac10,1; the four script files were exported from the working machine and synchronized byte-for-byte on 2026-11-07.**

The optical-drive (ODD) thermal-probe arrangement was relocated toward/on the SSD during the storage conversion. On the reference Linux system the ODD temperature reading was unavailable or invalid. The suite attempts to keep useful ODD fan cooling through *real* GPU, chipset and power-supply sensors rather than forcing a dangerously quiet fixed speed.

- [Suite README and architecture](fan-control-suite/README.md)
- [Magyar dokumentáció](fan-control-suite/README.hu.md)
- [Cooling daemon](fan-control-suite/scripts/imac-odd-fan.py)
- [macOS-inspired dark dashboard](fan-control-suite/scripts/imac-fan-control.py)
- [MATE status bar indicator](fan-control-suite/scripts/imac-panel-monitor.py)
- [Launcher, systemd and autostart examples](fan-control-suite/)

CPU and HDD fans retain firmware automatic control; optional boosts may only **increase** the minimum RPM. `0%` means no *additional* boost above the existing ODD thermal policy and factory HDD/CPU automatic behavior.

**Safety notice:** the scripts are exact exports from one modified iMac, but hardware-specific assumptions remain. **Do not install the daemon blindly or run alongside an existing fan-writing service.** Verify fan labels/limits and keep a recovery path. The systemd unit and desktop launcher templates have not been exported from the machine.

### 3. Bluetooth & Apple Wireless Keyboard — Blueman 2.4.3 case study

**Observed on the same iMac10,1 with its original Apple Bluetooth 2.0 + EDR controller.** The Ubuntu 24.04 Blueman 2.3.5 applet repeatedly crashed; the owner built and installed Blueman **2.4.3-1** and verified the package version. The Apple Bluetooth keyboard paired successfully. An embedded-keypad / Num Lock typing issue was also identified, with long-term fix verification still pending.

- [Bluetooth / Apple Keyboard troubleshooting (English)](docs/bluetooth-apple-keyboard.md)
- [Magyar útmutató](docs/bluetooth-apple-keyboard.hu.md)

**Status:** pairing and installed version confirmed; repeat-login crash regression and permanent keyboard fix are not yet confirmed.

## More documentation

- [Test machine and hardware checks](docs/hardware.md)
- [SSD conversion and ODD sensor case study](docs/ssd-upgrade.md)
- [Fan control safety and rollback](docs/thermal-safety.md)

## Roadmap

- [x] Export the four working scripts from the iMac and verify byte-for-byte Git blob checksums (2026-11-07)
- [ ] Review/sanitize hardware-specific paths and test on a second independently inspected iMac10,1
- [ ] Publish hardware-specific setup and screenshot examples
- [ ] Consolidate GPU/SSD/power management notes and performance benchmarks

## License and credits

[GPL-2.0-only](LICENSE) for project code and patches. The Linux kernel patch builds on upstream work by Gilles Risch and Alex Deucher; details and attribution remain in the [Radeon README](radeon-hd4850/README.md). No Apple proprietary files, commercial macOS assets, WhiteSur theme files or font files are distributed.

**Repository:** [`dxchild/imac10-1-linux-optimization`](https://github.com/dxchild/imac10-1-linux-optimization). The repository was renamed from its earlier Radeon-specific name.
