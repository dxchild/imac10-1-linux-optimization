# Bluetooth és Apple Wireless Keyboard – iMac10,1 (2009)

[English guide](bluetooth-apple-keyboard.md) · [Projekt főoldal](../README.hu.md)

## Eredmények (2026. november 9.)

**Tesztkörnyezet:** egy 2009-es iMac10,1, Ubuntu MATE 24.04, Linux `6.8.0-147-generic`.

- A rendszer felismeri a beépített **Apple Bluetooth 2.0 + EDR** adaptert: `05ac:8215`.
- Betöltődik a `btusb` driver; a vezérlő bekapcsolt állapotú és nincs blokkolva. A `bluetoothctl` eszközkeresés során új eszköz megjelenését jelezte.
- A gyári Ubuntu-csomagból telepített **Blueman 2.3.5-3build1** rendszeresen összeomlott: `/usr/bin/blueman-applet`, `gi.repository.GLib.GError`, `call_finish` (D-Bus művelet). A teljes belső D-Bus-hibaüzenet nem látható a rendelkezésre álló képernyőképeken.
- A tulajdonos Debian-forrásból elkészítette és telepítette a **Blueman 2.4.3-1** verziót. A telepített verziót az `dpkg-query` parancs igazolta.
- Az Apple Bluetooth-billentyűzet párosítása sikerült, billentyűleütéseket fogadott a rendszer. Egyes betűk helyett számok jelentek meg, ami összhangban lehet a régebbi kompakt billentyűzeteken elérhető numerikus réteg / Num Lock aktív állapotával. **A javítás tartóssága még nincs megerősítve.**

**Fontos:** az új Blueman-verzió telepítését és a sikeres párosítást igazoltuk, de a korábbi Blueman-összeomlás teljes megszűnését több újraindítás után még nem vizsgáltuk. A Bluetooth 2.0 + EDR adapter ettől nem válik BLE-kompatibilissé.

## Bluetooth-eszköz ellenőrzése

Az alábbi parancsokat **normál terminálban** futtasd (`user@host:~$`), nem a `[bluetooth]#` interaktív felületen.

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

A `Powered: yes` és a `Soft blocked: no` / `Hard blocked: no` jó jel, de önmagában még nem bizonyít sikeres párosítást.

Eszközkeresés:

```text
bluetoothctl
power on
agent on
default-agent
scan on
# A másik eszközt tedd párosítási módba.
devices
scan off
quit
```

**Gyakori hiba:** a `blueman-manager`, `sudo apt update` és más Linux-parancsok a `[bluetooth]#` prompt alatt nem működnek. Előbb a `quit` paranccsal vissza kell lépni a normál terminálba.

## Blueman-összeomlás és verzióváltás

A képernyőképeken látható hiba az Ubuntu 24.04 alatt:

```text
ExecutablePath: /usr/bin/blueman-applet
Package: blueman 2.3.5-3build1
ProblemType: Crash
gi.repository.GLib.GError in call_finish
```

A hibajelentés egy régebbi `libsqlite3-0` csomagra is figyelmeztetett, de ez **nem bizonyítja**, hogy az SQLite okozta az összeomlást.

Az iMac Ubuntu 24.04 tárolói nem kínáltak újabb Blueman-verziót. Az új változatot a Debian `2.4.3-1` forráscsomagjából fordítottuk helyben. A működő gépen ellenőrzött eredmény:

```console
$ dpkg-query -W -f='${Version}\n' blueman
2.4.3-1
```

**Példa a forráscsomag elkészítésére (haladó felhasználóknak, nem automatikus telepítő):**

```bash
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
sudo apt -s install ../blueman_2.4.3-1_amd64.deb
# Csak az apt szimuláció ellenőrzése után telepíts:
# sudo apt install ../blueman_2.4.3-1_amd64.deb
```

**Figyelmeztetés:** a Debian-csomag Ubuntu alatti telepítése eltér a disztribúció hivatalos csomagjaitól, és később kompatibilitási, illetve frissítési problémákat okozhat. Telepítés előtt ellenőrizd az `apt -s` által jelzett változtatásokat és tartsd meg a visszaállítás lehetőségét.

## Apple-billentyűzet: számok jelennek meg betűk helyett

A párosítás után egyes betűbillentyűk megnyomása számokat eredményezett. Ez **lehetséges Num Lock / beágyazott numerikus billentyűzet** probléma. A pontos billentyűzetmodelltől függően a Num Lock funkcióbillentyűvel kapcsolható, egyes modelleknél `Fn+F6` lehet.

X11/MATE alatt tesztelhető:

```bash
sudo apt install numlockx
numlockx off
```

Ezután újra próbáld a szövegbevitelt. **Csak akkor** érdemes autostart bejegyzést készíteni a `numlockx off` parancshoz, ha a fenti teszt valóban megoldotta. Ennek sikerességét a konkrét gépen még nem erősítettük meg. Ha magyar/angol billentyűkiosztás-eltérésről van szó, az XKB-kiosztást kell módosítani.

## Ellenőrzési lista

- [x] Beépített Apple Bluetooth-adapter felismerve
- [x] Bluetooth bekapcsolva, tiltás nélkül
- [x] Eszközkeresés működik
- [x] Blueman 2.4.3-1 telepítve
- [x] Apple Wireless Keyboard párosítva
- [ ] Újabb rendszerindítások után nincs Blueman-összeomlás
- [ ] Num Lock és karakterbevitel tartósan helyes
- [ ] További Bluetooth-eszközök tesztelése

A dokumentáció nem tartalmaz személyes Bluetooth MAC-címeket. Az útmutató a tesztgép tapasztalatait rögzíti, nem garantálja az eredményt minden iMacen.

Kapcsolódó fejlesztések: [Radeon-javítás](../radeon-hd4850/README.hu.md) · [Fan Control Suite](../fan-control-suite/README.hu.md).
