#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Community-tested iMac10,1 Radeon HD 4850 module rebuild.
# Does not install anything into /lib/modules or change boot settings.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KERNEL="6.8.0-147-generic"
BUILD="$HERE/build"
SOURCE="$BUILD/linux-source-6.8.0"
TARBALL="/usr/src/linux-source-6.8.0.tar.bz2"
UPSTREAM_COMMIT="275c3332585bbabcefad109a6978cc0cbecf2008"
UPSTREAM_PATCH="$BUILD/upstream-imac11-1.patch"
LOCAL_PATCH="$HERE/patches/0002-imac10-1-rv770-dce31-extension.patch"
TRACE="$SOURCE/drivers/gpu/drm/radeon/radeon_trace.h"

for binary in curl tar patch make modinfo grep sed; do
  command -v "$binary" >/dev/null || { echo "Missing tool: $binary" >&2; exit 1; }
done

[[ -f "$TARBALL" ]] || {
  echo "Missing Ubuntu 6.8 kernel source archive: $TARBALL" >&2
  exit 1
}
[[ -d "/lib/modules/$KERNEL/build" ]] || {
  echo "Missing matching $KERNEL headers" >&2
  exit 1
}
[[ -f "$LOCAL_PATCH" ]] || {
  echo "Missing local patch: $LOCAL_PATCH" >&2
  exit 1
}
[[ ! -e "$BUILD" ]] || {
  echo "Build directory already exists: $BUILD" >&2
  echo "Move it aside before rerunning this script." >&2
  exit 1
}

mkdir -p "$BUILD"
tar -xf "$TARBALL" -C "$BUILD"
[[ -f "$SOURCE/drivers/gpu/drm/radeon/atombios_crtc.c" ]] || {
  echo "Unexpected Ubuntu kernel source archive layout" >&2
  exit 1
}

curl -fLsS   "https://github.com/torvalds/linux/commit/${UPSTREAM_COMMIT}.patch"   -o "$UPSTREAM_PATCH"
grep -Fq "From ${UPSTREAM_COMMIT}" "$UPSTREAM_PATCH" || {
  echo "Upstream patch did not contain the expected commit ID; stopping" >&2
  exit 1
}

cd "$SOURCE"
patch --dry-run -p1 < "$UPSTREAM_PATCH"
patch -p1 < "$UPSTREAM_PATCH"
patch --dry-run -p1 < "$LOCAL_PATCH"
patch -p1 < "$LOCAL_PATCH"

# Stand-alone module compilation workaround, in this disposable tree only.
# The radeon_trace.h relative include in the original file assumes
# an in-kernel build; include this driver's source directory explicitly.
grep -q "TRACE_INCLUDE_PATH" "$TRACE" || {
  echo "TRACE_INCLUDE_PATH is missing; stopping" >&2
  exit 1
}
sed -i 's|^#define TRACE_INCLUDE_PATH .*|#define TRACE_INCLUDE_PATH .|' "$TRACE"
grep -Fq '#define TRACE_INCLUDE_PATH .' "$TRACE" || {
  echo "Trace include adjustment failed" >&2
  exit 1
}

make -C "/lib/modules/$KERNEL/build"   M="$SOURCE/drivers/gpu/drm/radeon"   KCFLAGS="-I$SOURCE/drivers/gpu/drm/radeon"   -j2 modules

KO="$SOURCE/drivers/gpu/drm/radeon/radeon.ko"
[[ -s "$KO" ]] || { echo "Module was not built: $KO" >&2; exit 1; }
VERMAGIC="$(modinfo -F vermagic "$KO")"
[[ "$VERMAGIC" == "$KERNEL "* ]] || {
  echo "Unexpected module vermagic: $VERMAGIC" >&2
  exit 1
}

printf '\nSUCCESS: Radeon module built at %s\n' "$KO"
printf 'vermagic: %s\n' "$VERMAGIC"
echo "NOT installed. Read README.md and arrange a rollback before installing."
