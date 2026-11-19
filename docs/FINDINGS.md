# Verified observations

Observed on 2026-11-19/20 on one HY300 Pro+; these observations do not establish
compatibility with another projector carrying the same retail name.

| Item | Observation |
| --- | --- |
| Display build | `projector.20250325.210225` |
| Android / ABI | Android 11 / `armeabi-v7a` |
| Hardware / platform | `sun50iw12p1` / `ares` |
| Running kernel | ARMv7 Linux 5.4.99 |
| SELinux | Permissive |
| Active slot | `_a` |
| Bootloader-reported vbmeta device state | `locked` |
| Main eMMC size | 7,818,182,656 bytes |
| Main eMMC node permission | `0666`; shell can read the raw disk |
| Individual boot node permission | `0600`, root-owned |
| `boot_a` start / size | 205824 sectors / 131072 sectors, 512 bytes each |
| `boot_b` start / size | 336896 sectors / 131072 sectors |
| `boot_a` header | `ANDROID!`, boot header v3 |
| `boot_b` header | Eight zero bytes; not a verified fallback |
| Standard `su` | Not found |
| Vendor `/system/bin/wifi root id` | Reports UID 0 |
| Vendor helper launching `sh -c id` | Drops to UID 2000; capability bounding set is restricted |
| Vendor helper launching `sh -p -c id` | Retains UID 0; permitted/effective capabilities zero, bounding mask 0xc0 |
| Stock network ADB setting | TCP port 5555 |
| USB-only ADB persistence | Reverts to port 5555 after reboot despite persistent port -1 |
| Stock launcher retained | `com.htc.spectraos` |

The retail H713 identity is consistent with the platform, CPU, and firmware
observations; the silicon package was not physically inspected.

## Package containment

The following packages were present, enabled, and successfully disabled for user 0:

- `com.htc.expandsdk`
- `com.htc.eventuploadservice`
- `com.htc.storeos`
- `com.hotack.screensaversdk`
- `com.htc.htcotaupdate`
- `android.rockchip.update.service`

`com.hotack.silentsdk` and `com.hotack.writesn` were not registered under those
package names in the inspected package list. That does not prove their code, or
other malicious code, is absent from firmware.

The package list and source reports support targeted containment, not attribution
of every listed app as malware. ExpandSDK is flagged as ad/persistence software
by the linked community research. Other components are disabled to reduce vendor
telemetry, background downloads, and unverified update/store activity. No packet
capture or complete APK reverse engineering was performed on this owner's unit.

## Backup and patch observations

The active boot image's SHA-256 was
`f84b6d2b890899012565f79a886633bd62656cd90b5e17590d9946531d1e4859`.
Its copy carved from the full-disk backup matched the separate boot backup.

Official Magisk v31.1 ARMv7 tools successfully produced a 64 MiB image on the
projector with `KEEPVERITY=true`, `KEEPFORCEENCRYPT=true`,
`PATCHVBMETAFLAG=false`, and `RECOVERYMODE=false`. Embedded vbmeta flags and the
main vbmeta flags were zero. Patching success alone is not boot verification.

A long raw ADB transfer stalled. The backup was resumed at a complete 1 MiB
boundary using bounded transfers; scripts now use bounded, size-checked chunks.
Remote dd status text must be redirected away from stdout, otherwise an apparently
successful stream can have extra bytes and fail size/header validation.

The resumed full private backup reached the expected 7,818,182,656 bytes and was
SHA-256 checksummed. It was acquired live; app state was changing, and containment
was applied during its final portion. Treat it as a recovery/research copy rather
than a consistent point-in-time backup of account databases. No restore was tested.
