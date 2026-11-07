# iMac10,1 (2009) – Linux Optimization Project

**Egy 2009-es Apple iMac felújítása és optimalizálása Ubuntu MATE alatt: működő Radeon grafika, SSD-átalakítás és intelligens hűtés.**

[English](README.md) · [Hardver](docs/hardware.md) · [Hűtésbiztonság](docs/thermal-safety.md)

> Közösségi projekt, **egyetlen konkrét iMac10,1 gépen szerzett tapasztalatokkal**. Nem hivatalos Apple-, Ubuntu- vagy Linux-fejlesztői kiadás.

## A projekt két működési területe

### Radeon HD 4850 / RV770 optimalizálás

A 2009-es, 27 hüvelykes, 2560×1440-es kijelzőjű iMac10,1 gépen a normál Linux Radeon indítás fekete képernyőt adott. A `nomodeset` csak szoftveres megjelenítést engedett. Egy eredeti Linux-javítás és két célzott módosítás együtt működő, gyorsított Radeon-megjelenítést eredményezett Ubuntu MATE 24.04 alatt, a `6.8.0-147-generic` kernellel.

[Részletes magyar útmutató](radeon-hd4850/README.hu.md) · [Angol technikai leírás](radeon-hd4850/README.md)

A korábbi `scripts/` és `patches/` útvonalakat megtartottuk a régi hivatkozások és parancsok kompatibilitásáért.

### iMac Fan Control Suite

A háttértár SSD-re cserélésekor az ODD (optikai meghajtó) hőérzékelőjének elhelyezése megváltozott: az érzékelőt / az érzékelő végét az SSD-hez helyeztük át. Ezen a tesztgépen a Linux által látott ODD-hőmérsékleti csatorna hibásnak vagy hiányzónak bizonyult.

A megoldás a GPU, a chipset és a tápegység hőmérséklete alapján szabályozza az ODD ventilátort, miközben a HDD és CPU ventilátor automatikus Apple SMC-üzemmódját megtartja. Az opcionális csúszkák csak **felfelé** módosíthatják a hűtési igényt, 0%-nál nincs hozzáadott gyorsítás.

A Suite részei: Python háttérprogram, sötét macOS-hangulatú grafikus főablak, felső MATE-paneles hőmérsékletkijelző, közös indító és automatikus indítás mintafájljai.

[Részletes magyar leírás](fan-control-suite/README.hu.md) · [Angol dokumentáció](fan-control-suite/README.md)

**Figyelem:** a GitHubra feltöltött Fan Suite forrásai a munkafolyamat alapján rekonstruált változatok; a valódi iMacen jelenleg futó fájlokkal még nem hasonlítottuk össze őket pontosan. Másik gépre vagy a működő hűtés helyére ellenőrzés nélkül telepíteni nem szabad.

## Dokumentáció

- [A tesztgép hardveradatai](docs/hardware.md)
- [SSD-csere és ODD-érzékelő](docs/ssd-upgrade.md)
- [Hővédelmi szabályok és visszaállítás](docs/thermal-safety.md)

## Fejlesztési terv

- [ ] A tesztgépen éppen futó háttérprogram és grafikus fájlok pontos feltöltése / összehasonlítása
- [ ] Ellenőrzés másik iMac10,1 hardveren
- [ ] Grafikus képernyőképek és biztonságos telepítési példák
- [ ] SSD-, fogyasztás- és teljesítményoptimalizálási dokumentáció

**Licenc:** [GPL-2.0-only](LICENSE), az eredeti Linux-fejlesztők szerzőségének megtartásával. A WhiteSur téma, Apple-eredetű fájlok és betűkészletek nem részei a projektnek.

**Repository név:** a GitHub-tároló egyelőre a régi `imac10-1-radeon-hd4850-linux-fix` nevet viseli; a tartalma már a tágabb iMac10,1 optimalizálási projekt. A tulajdonos a GitHub Settings felületen átnevezheti.
