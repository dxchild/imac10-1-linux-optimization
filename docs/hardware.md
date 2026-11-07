# Hardware profile — reference test machine

This document describes **one individual** late-2009 27-inch iMac. It is not a universal compatibility statement about all iMac10,1 configurations.

- DMI model: `iMac10,1`
- Internal panel: 2560×1440
- GPU: ATI/AMD Radeon HD 4850, RV770, 512 MB VRAM (`1002:944a`)
- OS for Radeon experiments: Ubuntu MATE 24.04 LTS, kernel `6.8.0-147-generic`
- Storage: SSD upgrade
- ODD thermal-sensing arrangement: the ODD-related sensor/probe was repositioned to the SSD area. Subsequent Linux Apple SMC readings for an ODD temperature channel were unavailable/invalid on this machine. Do not assume that a relocated probe *necessarily* means an electrically disconnected SMC channel on other Macs.
- Cooling: `applesmc` Linux driver reports three fans: ODD, HDD and CPU. Snapshot minimums were about 900, 1100 and 940 RPM respectively.
- After the original SSD/ODD modification: need to avoid a missing-sensor response with a quiet but responsive thermal policy rather than a static low-RPM override.

## Check your own hardware first

```bash
cat /sys/class/dmi/id/product_name
lspci -nn | grep -iE 'vga|display'
uname -r
sensors
for f in /sys/devices/platform/applesmc.*/fan{1,2,3}_{label,min,max,input,manual}; do
  echo "$f: $(cat "$f")"
done
```

Do not publish serial numbers or identifying terminal screenshots. DMI `product_name` is sufficient for an initial bug report.

## Related modules

- [Radeon HD 4850 internal display support](../radeon-hd4850/README.md)
- [Cooling suite](../fan-control-suite/README.md)
