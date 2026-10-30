# Radeon HD 4850 (RV770) internal-display fix for iMac10,1 on Linux

> **Community-tested workaround — not an official Ubuntu release.** Reported successful on **one** late-2009 Apple iMac reporting DMI `iMac10,1`, with Radeon HD 4850 (`1002:944a`), internal 2560×1440 display, Ubuntu MATE 24.04 LTS and **kernel `6.8.0-147-generic`**.

## What was fixed

- Stock Linux Radeon KMS: internal screen goes black.
- `nomodeset`: a desktop appears but Mesa uses CPU-based `llvmpipe`.
- Applying the upstream patch alone: moving/corrupted lines.
- Applying the additional iMac10,1-specific patch: stable internal desktop with Radeon GPU acceleration.

**Observed checks on the working system:**
```text
uname -r       → 6.8.0-147-generic
/proc/cmdline  → no nomodeset
glxinfo -B     → AMD RV770 (DRM 2.50.0 / 6.8.0-147-generic)
               → Accelerated: yes
               → Video memory: 512 MB
               → OpenGL 3.3
vainfo         → Mesa Gallium; H.264, VC-1, MPEG-2 decode profiles advertised
```

The VA-API profile listing does not by itself prove that every player can perform hardware video decoding.

A separate Linux 7.0.0-42 test showed unstable `ath9k` Wi-Fi on this individual machine; 6.8 worked. This is **not** a claim that kernel 7.0 is universally defective. This patch does not solve unrelated thermal-sensor or fan-control problems.

## Credits and patch details

This work **builds on** original upstream Linux commit [275c3332585bbabcefad109a6978cc0cbecf2008](https://github.com/torvalds/linux/commit/275c3332585bbabcefad109a6978cc0cbecf2008) — *drm/radeon: fix internal display on iMac11,1 (RV770/DCE3.1)*, authored by **Gilles Risch**, signed off by **Alex Deucher**.

That commit moves Apple's internal-display encoder **Link B** workaround so it also runs on the relevant `iMac10,1` display path. However, it limits two other display timing and activation conditions to `iMac11,1`.

Our experimental follow-up, [`patches/0002-imac10-1-rv770-dce31-extension.patch`](patches/0002-imac10-1-rv770-dce31-extension.patch), applied **after** that upstream commit, changes exactly two conditional checks from `iMac11,1` to `iMac10,1`:

1. `drivers/gpu/drm/radeon/atombios_crtc.c` — fractional feedback PLL divider for the high pixel clock (`RADEON_PLL_USE_FRAC_FB_DIV`).
2. `drivers/gpu/drm/radeon/atombios_encoders.c` — DP video enable after DP link training (`ATOM_ENCODER_CMD_DP_VIDEO_ON`).

**IMPORTANT:** this literal replacement was used to reproduce the one-machine test. It *replaces* the extra upstream quirk for iMac11,1 instead of broadening it to both models. **It is not upstream-ready and must not be used as-is for iMac11,1 or unrelated Macs.** Any generalization needs independent testing and upstream review.

## Rebuild the kernel module (does NOT install)

Keep a bootable Linux USB and a working fallback kernel available. The recipe targets the exact Ubuntu `6.8.0-147-generic` ABI; matching kernel headers and the Ubuntu 6.8 source package are required.

```bash
sudo apt update
sudo apt install -y build-essential patch curl kmod linux-source-6.8.0 linux-headers-6.8.0-147-generic
git clone https://github.com/dxchild/imac10-1-radeon-hd4850-linux-fix.git
cd imac10-1-radeon-hd4850-linux-fix
bash scripts/build-radeon.sh
```

The script downloads the **original upstream** patch, checks its commit ID, applies it to the Ubuntu kernel source, then applies the small local patch. It uses a disposable source tree and adjusts `TRACE_INCLUDE_PATH` to allow the tested stand-alone Radeon module build. The script deliberately **does not** install modules, edit GRUB, or reboot.

Check the compiled module:
```bash
modinfo -F vermagic build/linux-source-6.8.0/drivers/gpu/drm/radeon/radeon.ko
```
Expected prefix: `6.8.0-147-generic`. Matching `vermagic` is necessary, but not sufficient, for binary compatibility.

## Install and try it (advanced, reversible)

**Warning:** custom kernel modules can produce display corruption, a black screen or a system unable to boot graphically. Keep the original `nomodeset` fallback and a live USB. Secure Boot may reject unsigned modules.

From the repository root:
```bash
K=6.8.0-147-generic
KO="$PWD/build/linux-source-6.8.0/drivers/gpu/drm/radeon/radeon.ko"
test -s "$KO" || { echo "Module missing"; exit 1; }
modinfo -F vermagic "$KO"
mkdir -p "$HOME/radeon-recovery"
sudo cp -a "/boot/initrd.img-$K" "$HOME/radeon-recovery/initrd-before-fix-$K.img"
sudo mkdir -p "/lib/modules/$K/updates"
if [ -f "/lib/modules/$K/updates/radeon.ko" ]; then
  sudo cp -a "/lib/modules/$K/updates/radeon.ko" "$HOME/radeon-recovery/radeon-before-fix-$K.ko"
fi
sudo install -m 0644 "$KO" "/lib/modules/$K/updates/radeon.ko"
sudo depmod -a "$K"
sudo update-initramfs -u -k "$K"
modinfo -k "$K" -n radeon
```

That final path should end in `/lib/modules/6.8.0-147-generic/updates/radeon.ko`. An empty `lsinitramfs | grep radeon.ko` is not conclusive: the module can load later from disk. Work on the **target 6.8 kernel** is possible while another kernel is running.

For a **single test boot**, do not yet change the permanent GRUB defaults. Use rEFInd → Ubuntu **GRUB** (`grubx64.efi`) → Advanced options → 6.8.0-147. Press **e**, remove **only `nomodeset`** from the `linux` line, and boot with **Ctrl+X**. The underlying GRUB configuration remains unchanged for the next boot.

Verify:
```bash
uname -r
cat /proc/cmdline
modinfo -k 6.8.0-147-generic -n radeon
glxinfo -B
vainfo
```

Only after successful repeat boots consider changing `GRUB_DEFAULT` to `Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-147-generic` and removing `nomodeset` from `GRUB_CMDLINE_LINUX_DEFAULT`. Keep a known-good fallback and a backup of `/etc/default/grub` before editing.

## Rollback

If video is corrupt or black, reboot via GRUB with `nomodeset` added temporarily (or a working fallback kernel). Then:
```bash
K=6.8.0-147-generic
sudo rm -f "/lib/modules/$K/updates/radeon.ko"
sudo depmod -a "$K"
sudo update-initramfs -u -k "$K"
# Restore nomodeset to /etc/default/grub if permanently removed, then:
sudo update-grub
```
A saved module/initramfs can also be restored after verifying the backup. If unable to access the installed system, use a live USB and mount/chroot.

## Reporting bugs or successes

Include `cat /sys/class/dmi/id/product_name`, `lspci -nn`, `uname -r`, `glxinfo -B`, screen behavior and the exact patches applied. **Remove serial numbers, credentials, local usernames/paths and identifying photos** from submitted screenshots and logs.

## License

Patch and build script: [GPL-2.0-only](LICENSE), consistent with the modified Linux sources. The original upstream Linux authors retain their authorship and copyright; this repository does not claim the original kernel patch.

Magyarul: [README.hu.md](README.hu.md).
