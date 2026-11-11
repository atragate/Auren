# Developer reference

Normal users only need `../auren.py` and `../theme.json`.

`refind-source/` preserves the corrected local rEFInd 0.14.2 source. `refind-abi-fix.patch` records the change from the original custom build. `gnu-efi/` holds the Fedora 45 x86_64 GNU-EFI headers and libraries used for reproducibility, with their original documentation.

```bash
bash developer/build-bootloader.sh
```

This requires make, gcc, binutils and an x86_64 Linux host. It builds only the rEFInd core, using project-relative paths. It does not build GPTsync, sign binaries, copy anything to the EFI partition, enroll keys or change firmware entries.

The important fixes are a page-aligned SBAT section, matching the GNU-EFI library's Microsoft calling convention, preserving typed native calls, and retaining the native C ABI expected by GNU-EFI's entry shim. The previous convention mismatch prevented `SetMem` from clearing default utility slots, producing duplicate utilities even when `showtools` listed only four actions. The old harness failed and corrected harness passed; `validation.json` records that evidence.

The signed reference file was verified with the already enrolled local certificate. It is specific to that certificate and **must not be assumed trusted on another computer**. Private keys remain protected under `/etc/refind/keys` and are not in this repository. Any future executable update must be separately reviewed, signed and verified, then update the guard's pinned recovery pair under `/run/refind-integrity.lock`. The user-facing theme installer deliberately has no executable-install functionality.

Never run `objcopy --dump-section` directly against an installed signed PE executable without a separate output filename: it can rewrite the input and strip certificate bytes. Read PE sections from read-only bytes instead.

The diagnostic compiler tests and production signature/guard checks passed before migration. Testing new executable behavior on real firmware remains necessary after intentional future core changes.
