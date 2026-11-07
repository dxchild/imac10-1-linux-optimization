# Source snapshot — iMac10,1 Fan Control Suite

**Exported:** 2026-11-07 from the owner's working Ubuntu MATE iMac10,1 as `imac-fan-suite-source.zip`.

The four scripts below were uploaded byte-for-byte. Git returned the blob identifiers listed here, and each one was independently verified against the ZIP's local Git blob hash.

| Script | ZIP SHA-256 | Git blob SHA-1 |
|---|---|---|
| `scripts/imac-odd-fan.py` | `116ab50fc8cd3b41128814d6c5f3b4f092a1d4a94224205cb4cb3101d013993d` | `669646218d4a111fb6efdd9cc51931753d0b7969` |
| `scripts/imac-fan-control.py` | `3fb4fa5b1d726d8b28950f896e42aee9e2c8a80d1aa4494aeaaeeef1d56c2b10` | `36ace95addf945c04f81cf1c67cf61577ab41e99` |
| `scripts/imac-panel-monitor.py` | `2b53cb1c1e8d230ca58ca74ebd55a73c9ecde31ddf41b95dfa421e5c312fdb7e` | `26d0ed14556c717905d486d2e20c47c5cbc8c513` |
| `scripts/imac-fan-suite.sh` | `40fa51f1ce95e5cedd57e8c04866e53a086a73dc8a95cd9442afd191ae586264` | `a1c052db0f1fabf76680c036ee738da1c99b732a` |

## Important distinction

These scripts are **an exact snapshot, not a hardware-independent release**. The actual systemd unit, GRUB settings, fan profiles JSON file and desktop autostart entries were *not* included in the source ZIP. The files under `systemd/` and `desktop/` are examples derived from earlier configuration steps.

The exported daemon uses a machine-specific path `/home/imac/.config/imac-fan-curves.json`, and the fan order is assumed (fan1 ODD, fan2 HDD, fan3 CPU). The exported code does not automatically validate the fan-label order. **Review and adapt before deploying anywhere else.**

All Python scripts passed Python syntax parsing, and the shell script passed `bash -n`. **No hardware execution or system-level installation was performed by the GitHub sync.** The owner reports the package works on the source iMac.

To check an individual checked-out file later:

```bash
sha256sum fan-control-suite/scripts/imac-odd-fan.py
git hash-object fan-control-suite/scripts/imac-odd-fan.py
```

See [Thermal safety](../docs/thermal-safety.md).
