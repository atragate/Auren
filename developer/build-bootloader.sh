#!/usr/bin/env bash
# Developer-only rebuild. Does not sign, install or change firmware.
set -euo pipefail
dev_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(uname -m) == x86_64 ]] || { echo 'Bundled GNU-EFI libraries target x86_64.'; exit 1; }
for component in libeg mok gzip EfiLib refind; do
 make -C "$dev_root/refind-source/$component" MAKEWITH=GNUEFI \
  EFIINC="$dev_root/gnu-efi/usr/include/efi" GNUEFILIB="$dev_root/gnu-efi/usr/lib" \
  EFILIB="$dev_root/gnu-efi/usr/lib" EFICRT0="$dev_root/gnu-efi/usr/lib" \
  REFIND_SBAT_CSV=refind-sbat-z890.csv
done
echo "Unsigned output: $dev_root/refind-source/refind/refind_x64.efi"
echo 'No system files changed. Signing and installation require a separate review.'
