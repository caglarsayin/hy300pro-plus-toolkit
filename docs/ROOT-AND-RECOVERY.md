# Root and recovery status

The stock system offers no standard `su` command. A vendor SUID helper can report
UID 0 for individual commands but drops privileges on shell execution. Do not
treat that as a managed, reliable root installation.

A Magisk boot image has been prepared privately using the owner's own stock
image and the official Magisk release. Bootloader compatibility and a usable
restore path must be verified before a persistent flash. The bootloader reports
locked; the backup contains signed vbmeta structures. Do not assume verification
is disabled just because the main disk node has permissive permissions.

## Recovery boundaries

- Keep stock `boot_a`, vendor boot, vbmeta, bootloader, partition layout, and full
  disk copies private and checksum-verified.
- A raw disk image is not an Allwinner IMAGEWTY firmware package. Do not feed it
  directly to PhoenixUSBPro or a USB local-update menu.
- Fastboot support and its permission to write are separate questions. Read-only
  fastboot queries do not prove that a modified image will boot.
- Do not switch to B: it has not been verified as bootable on this unit.
- Do not run a bootloader unlock: it can erase user data.
- Do not disable vbmeta or write raw sectors until a build-specific recovery path
  has been validated. No generic sector-writing command is included in this kit.
- Hardware recovery may require physical access and a compatible Allwinner tool;
  a macOS ADB setup alone does not guarantee an unbrick path.

The release will record the actual test outcome below rather than imply that a
generated image has been tested.

## Bootloader test outcome

`adb reboot bootloader` disconnected ADB. `fastboot devices -l` returned no
projector on this Mac. A targeted USB inventory also found no Google/Allwinner
device identifier. This does not identify the exact internal boot mode, but it
means that the expected fastboot recovery route was unavailable in this session.
No partition was flashed, no bootloader unlock was requested, and no data was
erased. A physical power cycle is required to resume normal Android checks.

Containment has been applied successfully. A private, size-checked 7,818,182,656-byte
disk copy and private boot/recovery partition copies have been saved. Managed
Magisk root is **not installed or verified**. The patched image is a preparation
artifact, not a tested release. Do not flash it through the raw disk shortcut to
work around the missing recovery path.

An independently bootable recovery method or exact board-compatible stock update
package is needed before continuing persistent rooting. No compatible, fully
working faster custom ROM has been established for this build.
