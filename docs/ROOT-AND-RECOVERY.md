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
erased. The owner physically restarted the projector, which returned to its normal
home screen and authorized USB ADB.

Containment has been applied successfully. A private, size-checked 7,818,182,656-byte
disk copy and private boot/recovery partition copies have been saved. Managed
Magisk root is **not installed or verified**. The patched image is a preparation
artifact, not a tested release. Do not flash it through the raw disk shortcut to
work around the missing recovery path.

An independently bootable recovery method or exact board-compatible stock update
package is needed before continuing persistent rooting. No compatible, fully
working faster custom ROM has been established for this build.

## Normal-boot verification

After the physical restart, Android reported boot complete and all six targeted
packages remained disabled. The stock launcher, HDMI application, and focus
application were still installed. Wi-Fi remained disabled with no routes.

The vendor helper successfully executed the direct command
`setprop persist.adb.tcp.port -1`. `adb usb` then restarted ADB in USB mode.
The active property became `service.adb.tcp.port=0`, the persistent value was `-1`,
and the TCP listener list contained no port 5555. Normal Wi-Fi was left off and
can be enabled later through Settings; wireless streaming was not exercised.

A subsequent normal reboot completed and the six packages stayed disabled, but
`service.adb.tcp.port` reverted to `5555` and a TCP listener returned despite
`persist.adb.tcp.port=-1`. Therefore the USB-only workaround is session-scoped;
the release does not claim a persistent fix. The final handoff turns debugging
off entirely for normal use.

The final session set `adb_wifi_enabled=0` and `adb_enabled=0`. The transport
disconnected during the second command, and `adb devices -l` then showed no
devices. No further reboot or wireless traffic test was performed with debugging
off. Wi-Fi was left off; the owner can enable it in Settings for normal use.
