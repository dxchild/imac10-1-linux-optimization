# Magyar útmutató — iMac10,1 Radeon HD 4850 Linux javítás

**Kísérleti, egyetlen valódi gépen kipróbált javítás** a 2009-es, 27 hüvelykes Apple iMac (DMI: `iMac10,1`), Radeon HD 4850 / RV770 és 2560×1440-es belső kijelző kombinációjához.

**Tesztelt rendszer:** Ubuntu MATE 24.04 LTS, `6.8.0-147-generic` kernel.

## Mi volt a hiba?

Az eredeti Radeon-meghajtó normál KMS-indításkor fekete képernyőt adott. A `nomodeset` kapcsolóval volt kép, de csak `llvmpipe` szoftveres megjelenítéssel. A [hivatalos Linux-javítás](https://github.com/torvalds/linux/commit/275c3332585bbabcefad109a6978cc0cbecf2008) önmagában mozgó képcsíkokat eredményezett. Két további, kizárólag az `iMac10,1` modellre célzott forráskód-módosítás után a tesztgépen **stabil kép és Radeon hardveres gyorsítás** működött.

A működő gépen a `glxinfo -B` eredménye: **AMD RV770, Accelerated: yes, 512 MB videomemória, OpenGL 3.3**. A `vainfo` H.264/VC-1/MPEG-2 dekódolási profilokat hirdetett (ez nem bizonyítja önmagában a lejátszók tényleges hardveres dekódolását). A `nomodeset` többé nem volt szükséges.

## Mit tartalmaz a javítás?

Az eredeti Linux-javítás szerzője Gilles Risch; a módosítást Alex Deucher is aláírta. Az itt található **második patch** az eredeti módosítás utáni két `iMac11,1`-ellenőrzést `iMac10,1`-re cseréli:

1. `atombios_crtc.c`: speciális pixelórajel / PLL beállítás.
2. `atombios_encoders.c`: belső DisplayPort-videó engedélyezése.

**Figyelem:** ez célzott, nem általános kerneljavítás. A második patch *lecseréli* az iMac11,1-re vonatkozó ellenőrzést; más típusra nem javasolt változtatás nélkül. A hőérzékelő- és ventilátorhibákat nem javítja.

## Elkészítés

Az alábbi parancsokhoz internet, a pontos 6.8-as kernelhez tartozó fejlécek és működő tartalék indítás szükséges:

```bash
sudo apt update
sudo apt install -y git build-essential patch curl kmod linux-source-6.8.0 linux-headers-6.8.0-147-generic
git clone https://github.com/dxchild/imac10-1-radeon-hd4850-linux-fix.git
cd imac10-1-radeon-hd4850-linux-fix
bash scripts/build-radeon.sh
```

A szkript **csak a Radeon modult fordítja le**, nem telepíti, és nem módosítja a rendszerindítást.

A teljes telepítési, ellenőrzési és **visszaállítási** parancssorokat lásd az angol [README.md](README.md) dokumentumban. Ezeket olvasd végig, mielőtt bármilyen `radeon.ko` fájlt telepítesz.

## Biztonság és hibajelentés

Tarts meg egy működő kernelt és egy indítható Linux-pendrive-ot! Először csak **egyetlen indításra** távolítsd el a GRUB `nomodeset` kapcsolóját. Képhiba esetén indíts vissza `nomodeset` móddal. Az egyedi kernelmodul a frissített kernellel nem feltétlenül kompatibilis.

Más gépen elért eredményt az Issues részben lehet megosztani — típussal, kernelverzióval és `glxinfo -B` kimenettel. Személyes adatokat, sorozatszámokat és jelszavakat ne tölts fel.

**Licenc:** GPL-2.0-only; az eredeti Linux-fejlesztők szerzősége és jogai változatlanok.
