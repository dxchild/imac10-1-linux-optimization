# iMac Fan Control Suite – 2009-es iMac10,1

[English documentation](README.md)

> **Kísérleti, egy konkrét gépre készített megoldás.** A GitHubra feltöltött Python-fájlokat a működő rendszer kialakításának lépései alapján rekonstruáltuk, de a tulajdonos iMacén éppen futó fájlokkal **még nem vetettük össze bájtról bájtra**. Ezért a repository jelenleg tanulmányozási és tesztelési kiindulási alap, nem univerzális, automatikus telepítő.

## Miért készült?

A 2009-es, 27 hüvelykes iMac (DMI `iMac10,1`) háttértárát SSD-re cseréltük. Az átalakításkor az optikai meghajtóhoz (ODD) tartozó hőérzékelő elhelyezése is megváltozott: az érzékelőt / érzékelővezetéket az SSD irányába, illetve az SSD-re helyeztük át. A gépen Linux alatt az ODD eredeti hőmérsékleti csatornája hiányzónak vagy hibásnak bizonyult (például `-127 °C`, `-128 °C` értékek). Ez **ennek a gépnek a tapasztalata**, nem minden SSD-re átalakított iMac sajátossága.

A hibás vagy hiányzó ODD-hőadat miatt az Apple SMC ventilátorszabályozása nem feltétlenül működik a megszokott módon. Egy fix, alacsony fordulatszám ugyan halkabb lehetne, de könnyen túlmelegedéshez vezethet.

A program célja ezért: **csendesebb, de a GPU/chipset/tápegység valós melegedésére reagáló hűtés**, miközben a HDD és a CPU ventilátor eredeti automatikus szabályozását megtartjuk.

## A csomag részei

- [`scripts/imac-odd-fan.py`](scripts/imac-odd-fan.py) – háttérszolgáltatás, ODD ventilátor hőmérsékletfüggő vezérlése és opcionális HDD/CPU minimumfordulat-emelés.
- [`scripts/imac-fan-control.py`](scripts/imac-fan-control.py) – sötét, Mac-hangulatú grafikus vezérlő, három beállítható hűtési görbével.
- [`scripts/imac-panel-monitor.py`](scripts/imac-panel-monitor.py) – GPU-hőmérséklet a MATE felső paneljén, lenyíló részletes adatokkal.
- [`scripts/imac-fan-suite.sh`](scripts/imac-fan-suite.sh) – közös grafikus indító, duplikált folyamatok nélkül.
- [`systemd/imac-odd-fan.service`](systemd/imac-odd-fan.service) – rendszerindításkor futó vezérlő mintaszolgáltatása.
- [`desktop/imac-fan-suite.desktop`](desktop/imac-fan-suite.desktop) – MATE-bejelentkezéskor induló grafikus összetevők mintája.

A **grafikus ablak bezárása nem állítja le a háttérben futó ventilátorvezérlést**.

## Milyen szenzorokat figyel?

| Szenzor | Jelentés |
|---|---|
| `TG0D / TG0H / TG0P` | GPU és környezete |
| `TN0H` | Alaplapi chipset |
| `Tp2H` | Tápegység hőmérsékleti pontja |
| `TC0H`, `coretemp` | CPU-hűtőborda és processzormagok |
| `Tm0P / TM0P` | Alaplaphoz közeli hőmérséklet |

A hibás (pl. `-127 °C`) adatok kiesnek a mérésekből.

## A három ventilátor

**ODD:** az eredeti ODD-szenzor helyett a GPU, a chipset és a tápegység érzékelőinek külön hűtési igényeit használjuk; a legmagasabb kérés érvényesül. Fontos szenzorhiba esetén a biztonságos irány a maximális fordulat.

**HDD és CPU:** a gyári automatikus módot meghagyjuk, csak a megengedett *minimumfordulatot* emelhetjük. A HDD-hez felhasznált környezeti hőmérséklet nem azonos az SSD belső SMART-hőmérsékletével.

**0% = nincs hozzáadott gyorsítás.** Az ODD saját hővédelmi alapgörbéje és a HDD/CPU gyári szabályozása működik tovább. 0% fölött csak nagyobb hűtést lehet kérni. A rajzolt görbék a szoftveres kérésre, nem a gyári automata teljes belső algoritmusára vonatkoznak.

**Ezen az iMacen mért ventilátorsorrend:** 1 = ODD, 2 = HDD, 3 = CPU. **Mért minimumok:** 900, 1100, 940 RPM. Másik iMacen ezeket ellenőrzés nélkül használni veszélyes.

## Előzetes, csak olvasó ellenőrzés

```bash
cat /sys/class/dmi/id/product_name
sensors
for f in /sys/devices/platform/applesmc.*/fan{1,2,3}_{label,min,max,manual,input}; do echo "$f: $(cat "$f")"; done
```

**Ne másold fel automatikusan a háttérprogramot másik gépre.** Ellenőrizni kell az Apple SMC útvonalakat, az érzékelők érvényességét, a ventilátorok feliratait, a minimumokat és a védelmi küszöböket.

Ubuntu MATE grafikus függőségek:

```bash
sudo apt install python3 python3-tk python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

A felső panelhez Indicator Applet Complete vagy azzal kompatibilis kisalkalmazás szükséges.

**Biztonsági telepítési és visszaállítási részletek:** [angol README](README.md) és [Thermal safety](../docs/thermal-safety.md).

## Állapot, licenc

Az eredeti gépen a hűtés és a grafikus felület működik, de a GitHub-forrás **még rekonstruált referencia**, a gépen futó pontos állapot feltöltése és a szélesebb körű tesztelés hátravan.

[GPL-2.0-only](../LICENSE). A WhiteSur téma és az Inter betűtípus nem része a repositorynak.
