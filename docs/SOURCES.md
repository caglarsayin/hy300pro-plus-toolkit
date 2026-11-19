# Sources

Consulted 2026-11-19/20. External guides describe other units and can change.

- [well0nez/magcubic-root](https://github.com/well0nez/magcubic-root): H713
  firmware repacking, package investigation, and raw eMMC access reports.
- [Kavan00/Android-Projector-C2-Malware](https://github.com/Kavan00/Android-Projector-C2-Malware):
  primary investigation of the projector malware ecosystem.
- [YuujiLab H713 research](https://github.com/YuujiLab/HY300-H713-Research):
  boot, partition, recovery, and GSI research on a related owner device.
- [YuujiLab Magisk guide](https://github.com/YuujiLab/HY300-H713-Research/blob/main/Root/MAGISK_GUIDE.md):
  reports a Magisk root method; not proof that this build accepts flashing.
- [YuujiLab GSI findings](https://github.com/YuujiLab/HY300-H713-Research/blob/main/GSI/GSI_DISCOVERIES.md):
  reports display/compositor failures; no verified faster replacement ROM is
  established for this owner's unit.
- [Official Magisk installation guide](https://topjohnwu.github.io/Magisk/install.html):
  use the owner's own boot image; keep the original for recovery.
- [Official Magisk v31.1 release](https://github.com/topjohnwu/Magisk/releases/tag/v31.1):
  downloaded APK SHA-256
  `89cefac0a318afa39fb3880c45c87b036c05bc1ebf02a7a715b7f8d7c26ac6e7`.

Device observations in FINDINGS.md were collected separately in the owner session.
No upstream source text or device firmware binaries are bundled.
