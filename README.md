# HY300 Pro+ H713 containment and boot preparation

Tools and measured findings from one owner-authorized HY300 Pro+ running
`projector.20250325.210225`, Android 11, `sun50iw12p1` / `ares`, ARMv7 userspace.
Model names are reused across different boards. Mutating commands refuse other
hardware/builds. This project does not provide a universal ROM or certify a device
as malware-free.

## Start here

Install Python 3 and Google's Android platform-tools. Enable USB debugging on the
projector and authorize your computer on its display. Connect using a confirmed
device/OTG data port and an appropriate cable; do not assume a generic powered
USB-A host port is safe for a USB-A-to-USB-A connection.

```sh
adb devices -l
python3 scripts/projector.py inspect
python3 scripts/projector.py isolate
python3 scripts/projector.py backup --out "$HOME/hy300-private-backup" --full
python3 scripts/projector.py contain --state "$HOME/hy300-private-backup/containment-state.json"
```

The full backup needs approximately 8 GB free space, plus working space. Keep the
projector powered and connected. An incomplete backup is not usable. The manifest
records byte sizes and SHA-256 hashes. A live backup is not an atomic snapshot of
Android's changing app databases, and having a raw dump does not establish a
working recovery/flashing procedure.

`contain` saves previous enablement state, disables selected packages for user 0,
and verifies each result. It preserves the launcher, focus, projection controls,
and HDMI services. Package files stay in firmware; a reset or privileged component
could restore them. Firmware-level removal and traffic verification require
additional work.

## Roll back containment

```sh
python3 scripts/projector.py restore --state "$HOME/hy300-private-backup/containment-state.json"
```

Only packages changed by this tool are re-enabled. Wi-Fi stays off until you
enable it in Settings. Do not overwrite the original rollback state by running
containment again with the same filename.

## Build a private Magisk boot image

Use your own verified `boot_a.img` from the backup. The patch script downloads
Magisk v31.1 from its official release and checks a pinned SHA-256 digest. It runs
the official ARMv7 patch tools on the connected owner device, preserving verity
and encryption settings. It does not flash or install the app.

```sh
shasum -a 256 "$HOME/hy300-private-backup/boot_a.img"
python3 scripts/patch_boot.py \
  --stock "$HOME/hy300-private-backup/boot_a.img" \
  --stock-sha256 YOUR_OWN_STOCK_SHA256 \
  --out "$HOME/hy300-private-patch"
```

Successful patching does not prove the image will boot. See
[root and recovery status](docs/ROOT-AND-RECOVERY.md) before considering a flash.
Do not unlock, wipe, change slots, or overwrite vbmeta based on a generic tutorial.
Slot B did not contain an Android boot header on the tested unit and is not a
verified fallback.

## Wireless use

Wi-Fi hardware and normal streaming remain available. Use Settings to enable
Wi-Fi when ready, preferably on a guest/IoT network that cannot access your other
devices. Keep network debugging off. The tested stock image exposed ADB on TCP
5555; the owner session switches ADB to USB-only. Recheck after every reboot and
firmware update because vendor services may change settings.

```sh
adb usb
adb shell getprop service.adb.tcp.port
adb shell getprop persist.adb.tcp.port
```

`service.adb.tcp.port` should be `-1` (or disabled by the platform), not `5555`.
`adb usb` restarts the daemon and may briefly disconnect it. It does not disable
normal Wi-Fi. ADB authorization and settings are separate from a malware audit.

## Privacy and release contents

**Never publish a full eMMC dump, userdata, `/data`, `/oem/customer.prop`, saved
network settings, arbitrary getprop dumps, logs, APKs pulled from user storage, or
account databases.** They can contain tokens, passwords, identifiers, vendor keys,
and personal files. Full stock firmware also contains the original suspect code.

No stock or patched device binaries are distributed here. Build your own images
from your own device. Release archives include only explicit source/documentation
allowlists. File extensions are also ignored by Git as a second layer; `.gitignore`
alone is not a privacy review. Boot hashes identify bytes, not safety or universal
compatibility.

Read [verified findings](docs/FINDINGS.md), [root status](docs/ROOT-AND-RECOVERY.md),
and [sources](docs/SOURCES.md). Run safety checks with:

```sh
python3 -m unittest discover -s tests -v
```

Original scripts are licensed under the MIT License. Upstream tools retain their
own licenses and are downloaded separately. Community research is linked rather
than redistributed.
