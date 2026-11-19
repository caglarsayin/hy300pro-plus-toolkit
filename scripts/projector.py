#!/usr/bin/env python3
"""USB-only inventory, backup, and reversible containment for one H713 build.

No boot flashing or filesystem deletion is performed by this program.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

BUILD = 'projector.20250325.210225'
HARDWARE = 'sun50iw12p1'
PACKAGES = (
    'com.htc.expandsdk',
    'com.htc.eventuploadservice',
    'com.htc.storeos',
    'com.hotack.screensaversdk',
    'com.htc.htcotaupdate',
    'android.rockchip.update.service',
    'com.hotack.silentsdk',
    'com.hotack.writesn',
)
PROPS = ('ro.hardware', 'ro.board.platform', 'ro.product.cpu.abi',
         'ro.build.display.id', 'ro.build.version.release',
         'ro.boot.slot_suffix', 'ro.boot.vbmeta.device_state')


class Device:
    def __init__(self, serial):
        self.serial = serial

    def adb(self, *args, **kwargs):
        return subprocess.run(['adb', '-s', self.serial, *args],
                              check=True, **kwargs)

    def shell(self, command):
        return self.adb('shell', command, capture_output=True,
                        text=True).stdout.strip()

    def prop(self, key):
        return self.shell('getprop ' + shlex.quote(key))

    def guard(self):
        if self.prop('ro.hardware') != HARDWARE or self.prop('ro.build.display.id') != BUILD:
            raise RuntimeError('Unsupported hardware/build; inventory is allowed, mutations are refused.')
        if self.prop('ro.boot.slot_suffix') != '_a':
            raise RuntimeError('Expected active slot _a. Never switch to the unverified B slot.')


def select_device(serial=None):
    lines = subprocess.check_output(['adb', 'devices', '-l'], text=True).splitlines()
    devices = []
    for line in lines:
        fields = line.split()
        if len(fields) > 1 and fields[1] == 'device' and any(f.startswith('usb:') for f in fields):
            devices.append(fields[0])
    if serial:
        if serial not in devices:
            raise RuntimeError('Requested device is not authorized over USB.')
        return Device(serial)
    if len(devices) != 1:
        raise RuntimeError('Connect exactly one authorized USB ADB device, or supply --serial.')
    return Device(devices[0])


def partition_map(device):
    result = {}
    names = device.shell('ls /dev/block/by-name').splitlines()
    for name in names:
        if not re.fullmatch(r'[A-Za-z0-9_]+', name) or name == 'mmcblk0':
            continue
        node = device.shell('readlink -f /dev/block/by-name/' + name)
        match = re.fullmatch(r'/dev/block/(mmcblk0p[0-9]+)', node)
        if not match:
            continue
        part = match.group(1)
        root = '/sys/block/mmcblk0/' + part
        result[name] = dict(node=node,
                           start_sector=int(device.shell('cat ' + root + '/start')),
                           sectors=int(device.shell('cat ' + root + '/size')))
    return result


def inventory(device):
    # Deliberately omit serial, fingerprints, network addresses, and arbitrary getprop output.
    return {'properties': {k: device.prop(k) for k in PROPS},
            'selinux': device.shell('getenforce'),
            'shell_identity': device.shell('id'),
            'disk_sectors': int(device.shell('cat /sys/block/mmcblk0/size')),
            'partitions': partition_map(device),
            'installed_packages': device.shell('pm list packages').splitlines()}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def backup(device, directory, full=False):
    device.guard()
    directory = Path(directory).expanduser()
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    data = inventory(device)
    files = {}
    targets = [('boot_a', data['partitions']['boot_a']),
               ('boot_b', data['partitions']['boot_b'])]
    if full:
        targets.append(('emmc-private', {'start_sector': 0, 'sectors': data['disk_sectors']}))
    for name, info in targets:
        path = directory / (name + '.img')
        expected = info['sectors'] * 512
        print('Reading', name, expected, 'bytes', flush=True)
        with path.open('xb') as f:
            os.chmod(path, 0o600)
            # Bounded streams avoid a long-running exec-out transfer stalling.
            # stderr must stay out of the binary stream: remote dd may append statistics.
            offset = 0
            while offset < expected:
                sectors = min(262144, info['sectors'] - offset // 512)
                start = info['start_sector'] + offset // 512
                command = (f'dd if=/dev/block/mmcblk0 bs=512 skip={start} '
                           f'count={sectors} 2>/dev/null')
                chunk = device.adb('exec-out', command, capture_output=True, timeout=120).stdout
                if len(chunk) != sectors * 512:
                    raise RuntimeError(f'Short backup chunk at byte {offset}; do not use this backup.')
                f.write(chunk)
                f.flush()
                offset += len(chunk)
                print(f'  {offset}/{expected}', flush=True)
        if path.stat().st_size != expected:
            raise RuntimeError('Short backup: ' + str(path))
        with path.open('rb') as f:
            header = f.read(8)
        if name == 'boot_a' and header != b'ANDROID!':
            raise RuntimeError('Active boot image has an unexpected header.')
        files[path.name] = {'size': expected, 'sha256': sha256(path),
                            'android_boot_header': header == b'ANDROID!'}
    data['files'] = files
    (directory / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n')
    print('Private backup complete:', directory)
    print('A live full-disk copy is not an atomic snapshot; protect it as credential-bearing data.')


def isolate(device):
    device.guard()
    device.shell('svc wifi disable')
    for _ in range(15):
        status = device.shell('cmd wifi status')
        ipv4 = device.shell('ip route')
        ipv6 = device.shell('ip -6 route')
        if 'Wifi is disabled' in status and not ipv4 and not ipv6:
            print('Wi-Fi disabled; IPv4 and IPv6 routing tables empty.')
            return
        time.sleep(1)
    raise RuntimeError('Network isolation could not be verified. Unplug Ethernet and inspect Wi-Fi.')


def contain(device, state_file):
    device.guard()
    isolate(device)
    state_file = Path(state_file).expanduser()
    if state_file.exists():
        raise RuntimeError('State file exists; preserve the original rollback state.')
    installed = set(device.shell('pm list packages').splitlines())
    disabled = set(device.shell('pm list packages -d').splitlines())
    state = {'build': BUILD, 'hardware': HARDWARE, 'packages': {}}
    for package in PACKAGES:
        if 'package:' + package in installed:
            state['packages'][package] = {'was_disabled': 'package:' + package in disabled,
                                          'disabled_by_tool': False}
    state_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    def save():
        state_file.write_text(json.dumps(state, indent=2) + '\n')
        state_file.chmod(0o600)
    save()
    failures = []
    for package, previous in state['packages'].items():
        if previous['was_disabled']:
            continue
        result = device.shell('pm disable-user --user 0 ' + package)
        current = device.shell('pm list packages -d').splitlines()
        if 'package:' + package not in current:
            failures.append(package)
            print('FAILED', package, result)
        else:
            previous['disabled_by_tool'] = True
            save()
            device.shell('am force-stop --user 0 ' + package)
            print('Disabled', package)
    if failures:
        raise RuntimeError('Not all packages were disabled: ' + ', '.join(failures))
    print('Containment complete. System APK files remain; this is not a clean-ROM attestation.')


def restore(device, state_file):
    device.guard()
    state = json.loads(Path(state_file).expanduser().read_text())
    if state.get('build') != BUILD or state.get('hardware') != HARDWARE:
        raise RuntimeError('Rollback state is for another build.')
    for package, previous in state['packages'].items():
        if package not in PACKAGES:
            raise RuntimeError('Unknown package in state file.')
        if previous['disabled_by_tool'] and not previous['was_disabled']:
            print(device.shell('pm enable --user 0 ' + package))
            if 'package:' + package in device.shell('pm list packages -d').splitlines():
                raise RuntimeError('Package restoration failed: ' + package)
    print('Restored package enablement. Wi-Fi remains off; enable it in Settings when ready.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('inspect')
    sub.add_parser('isolate')
    p = sub.add_parser('backup')
    p.add_argument('--out', required=True)
    p.add_argument('--full', action='store_true')
    for action in ('contain', 'restore'):
        p = sub.add_parser(action)
        p.add_argument('--state', required=True)
    args = parser.parse_args()
    d = select_device(args.serial)
    if args.action == 'inspect':
        print(json.dumps(inventory(d), indent=2))
    elif args.action == 'backup':
        backup(d, args.out, args.full)
    elif args.action == 'isolate':
        isolate(d)
    elif args.action == 'contain':
        contain(d, args.state)
    else:
        restore(d, args.state)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError, KeyError) as exc:
        sys.exit(str(exc))
