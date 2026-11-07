# SSD conversion and ODD thermal sensor — case study

The 2009 iMac in this project was upgraded from its original storage arrangement to an SSD. During the hardware conversion, the optical-drive/ODD temperature probe arrangement was changed, with the sensor relocated to the SSD area.

On **this single machine**, reading Apple SMC sensors under Linux showed values such as `-127 °C` and `-128 °C` on some channels, which are not plausible temperatures. We treated them as invalid readings. The ODD temperature sensor was not available as a reliable input for ordinary automatic cooling.

The aim of our `fan-control-suite` is to retain effective thermal protection:
1. Monitor independent GPU (`TG0*`), chipset (`TN0H`) and PSU (`Tp2H`) temperatures.
2. Let the ODD fan respond to the most demanding of these separate sensors.
3. Preserve firmware auto mode on HDD and CPU fans, applying only optional upward minimum-RPM boosts.
4. Use a fail-safe higher ODD RPM if required temperature data disappears.

**Important distinction:** physically relocating a probe is not always the same as losing its electrical reading; cable routing, connection, drive bay used and SMC behavior vary. The reason for the invalid reading on this particular machine has not been independently verified with the original wiring restored. Please don't use this as instructions to disconnect, bypass, or relocate a working fan sensor.

The software is intended as a **hardware-specific workaround**, not a substitute for a correctly installed SSD sensor adapter and full hardware thermal inspection.

See [fan control documentation](../fan-control-suite/README.md) and [thermal safety](thermal-safety.md).
