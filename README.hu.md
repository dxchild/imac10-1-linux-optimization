# iMac10,1 (2009) – Linux Optimization Project

**Egy 2009-es Apple iMac felújítása és optimalizálása Ubuntu MATE alatt: működő Radeon grafika, SSD-átalakítás és intelligens hűtés.**

[English](README.md) · [Hardver](docs/hardware.md) · [Hűtésbiztonság](docs/thermal-safety.md)

> Közösségi projekt, **egyetlen konkrét iMac10,1 gépen szerzett tapasztalatokkal**. Nem hivatalos Apple-, Ubuntu- vagy Linux-fejlesztői kiadás.

## A projekt fő területei

### Radeon HD 4850 / RV770 optimalizálás

A 2009-es, 27 hüvelykes, 2560×1440-es kijelzőjű iMac10,1 gépen a normál Linux Radeon indítás fekete képernyőt adott. A `nomodeset` csak szoftveres megjelenítést engedett. Egy eredeti Linux-javítás és két célzott módosítás együtt működő, gyorsított Radeon-megjelenítést eredményezett Ubuntu MATE 24.04 alatt, a `6.8.0-147-generic` kernellel.

[Részletes magyar útmutató](radeon-hd4850/README.hu.md) · [Angol technikai leírás](radeon-hd4850/README.md)

A korábbi `scripts/` és `patches/` útvonalakat megtartottuk a régi hivatkozások és parancsok kompatibilitásáért.

### iMac Fan Control Suite

A háttértár SSD-re cserélésekor az ODD (optikai meghajtó) hőérzékelőjének elhelyezése megváltozott: az érzékelőt / az érzékelő végét az SSD-hez helyeztük át. Ezen a tesztgépen a Linux által látott ODD-hőmérsékleti csatorna hibásnak vagy hiányzónak bizonyult.

A megoldás a GPU, a chipset és a tápegység hőmérséklete alapján szabályozza az ODD ventilátort, miközben a HDD és CPU ventilátor automatikus Apple SMC-üzemmódját megtartja. Az opcionális csúszkák csak **felfelé** módosíthatják a hűtési igényt, 0%-nál nincs hozzáadott gyorsítás.

A Suite részei: Python háttérprogram, sötét macOS-hangulatú grafikus főablak, felső MATE-paneles hőmérsékletkijelző, közös indító és automatikus indítás mintafájljai.

[Részletes magyar leírás](fan-control-suite/README.hu.md) · [Angol dokumentáció](fan-control-suite/README.md)

**Figyelem:** a négy Fan Suite-szkriptet 2026. november 7-én az iMacről exportált ZIP alapján, pontos Git blob-ellenőrzéssel szinkronizáltuk. Ettől még gépspecifikusak: másik iMacre ellenőrzés nélkül nem telepíthetők. A systemd és autostart fájlok továbbra is dokumentációs minták.

### Bluetooth és Apple Wireless Keyboard

A gyári Apple Bluetooth 2.0 + EDR adapter működik az iMac10,1 alatt. Az Ubuntu MATE 24.04 gyári Blueman **2.3.5** programja rendszeresen összeomlott, ezért Debian-forrásból elkészült és felkerült a **Blueman 2.4.3-1**. Az Apple Bluetooth-billentyűzetet sikerült párosítani. Egy betűk helyett számokat adó, valószínűleg Num Lockhoz kapcsolódó jelenséget is vizsgáltunk.

[Bluetooth és Apple-billentyűzet javítás – magyar útmutató](docs/bluetooth-apple-keyboard.hu.md) · [English guide](docs/bluetooth-apple-keyboard.md)

**Állapot:** telepített verzió és párosítás igazolva; az összeomlás tartós megszűnését és a Num Lock megoldását újraindítás után még ellenőrizni kell.

## Dokumentáció

- [A tesztgép hardveradatai](docs/hardware.md)
- [SSD-csere és ODD-érzékelő](docs/ssd-upgrade.md)
- [Hővédelmi szabályok és visszaállítás](docs/thermal-safety.md)

## Fejlesztési terv

- [x] A tesztgépről exportált négy szkript pontos feltöltése és ellenőrzése (2026-11-07)
- [ ] Hardverspecifikus útvonalak felülvizsgálata és ellenőrzés másik iMac10,1 gépen
- [ ] Grafikus képernyőképek és biztonságos telepítési példák
- [ ] SSD-, fogyasztás- és teljesítményoptimalizálási dokumentáció

**Licenc:** [GPL-2.0-only](LICENSE), az eredeti Linux-fejlesztők szerzőségének megtartásával. A WhiteSur téma, Apple-eredetű fájlok és betűkészletek nem részei a projektnek.

**Repository:** [`dxchild/imac10-1-linux-optimization`](https://github.com/dxchild/imac10-1-linux-optimization). A korábbi Radeon-specifikus elnevezésről már át lett nevezve.
