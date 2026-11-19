#!/usr/bin/env python3
"""Patch your own boot image on the connected projector. Does not flash it."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys
import urllib.request
import zipfile

from projector import BUILD, select_device, sha256

VERSION = '31.1'
APK_SHA256 = '89cefac0a318afa39fb3880c45c87b036c05bc1ebf02a7a715b7f8d7c26ac6e7'
URL = f'https://github.com/topjohnwu/Magisk/releases/download/v{VERSION}/Magisk-v{VERSION}.apk'
REMOTE = '/data/local/tmp/hy300-owner-patch'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial')
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--stock-sha256', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    d = select_device(a.serial)
    d.guard()
    if a.stock.stat().st_size != 67108864 or sha256(a.stock) != a.stock_sha256:
        sys.exit('Stock image size/checksum mismatch.')
    with a.stock.open('rb') as f:
        if f.read(8) != b'ANDROID!':
            sys.exit('Not an Android boot image.')
    a.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    apk = a.out / f'Magisk-v{VERSION}.apk'
    with urllib.request.urlopen(URL, timeout=60) as response, apk.open('xb') as f:
        while chunk := response.read(1024 * 1024):
            f.write(chunk)
    if sha256(apk) != APK_SHA256:
        sys.exit('Magisk APK checksum mismatch; refusing execution.')
    tools = a.out / 'tools'
    tools.mkdir()
    with zipfile.ZipFile(apk) as z:
        for name in ('boot_patch.sh', 'util_functions.sh'):
            (tools / name).write_bytes(z.read('assets/' + name))
        for name in ('magisk', 'magiskboot', 'magiskinit', 'init-ld'):
            target = tools / name
            target.write_bytes(z.read('lib/armeabi-v7a/lib' + name + '.so'))
            target.chmod(0o755)
    d.adb('shell', 'mkdir -p ' + REMOTE)
    for file in tools.iterdir():
        d.adb('push', str(file), REMOTE + '/' + file.name)
    d.adb('push', str(a.stock), REMOTE + '/boot.img')
    d.adb('shell', f'cd {REMOTE} && BOOTMODE=true KEEPVERITY=true '
          'KEEPFORCEENCRYPT=true PATCHVBMETAFLAG=false RECOVERYMODE=false '
          'sh ./boot_patch.sh boot.img')
    patched = a.out / 'boot_a-magisk.img'
    d.adb('pull', REMOTE + '/new-boot.img', str(patched))
    patched.chmod(0o600)
    if patched.stat().st_size != a.stock.stat().st_size:
        sys.exit('Patched image size mismatch; do not flash.')
    manifest = {'build': BUILD, 'magisk_version': VERSION,
                'apk_sha256': APK_SHA256,
                'stock_sha256': sha256(a.stock), 'patched_sha256': sha256(patched),
                'flashed': False,
                'note': 'Generated on owner device. Never distribute as universal firmware.'}
    (a.out / 'patch-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared only; no partitions flashed:', patched)


if __name__ == '__main__':
    main()
