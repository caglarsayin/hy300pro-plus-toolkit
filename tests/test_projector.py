import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('projector', Path(__file__).parents[1] / 'scripts/projector.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class GuardTests(unittest.TestCase):
    def test_other_build_is_rejected(self):
        d = p.Device('unused')
        d.prop = lambda key: {'ro.hardware': p.HARDWARE, 'ro.build.display.id': 'other'}[key]
        with self.assertRaises(RuntimeError):
            d.guard()

    def test_wrong_slot_is_rejected(self):
        d = p.Device('unused')
        values = {'ro.hardware': p.HARDWARE, 'ro.build.display.id': p.BUILD, 'ro.boot.slot_suffix': '_b'}
        d.prop = values.__getitem__
        with self.assertRaises(RuntimeError):
            d.guard()

    def test_network_adb_cannot_be_selected(self):
        output = 'List of devices attached\n192.0.2.1:5555 device product:adt3\n'
        with patch.object(p.subprocess, 'check_output', return_value=output):
            with self.assertRaises(RuntimeError):
                p.select_device()

    def test_multiple_usb_devices_require_serial(self):
        output = 'List of devices attached\na device usb:1\nb device usb:2\n'
        with patch.object(p.subprocess, 'check_output', return_value=output):
            with self.assertRaises(RuntimeError):
                p.select_device()
            self.assertEqual(p.select_device('b').serial, 'b')

    def test_digest_reads_binary_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'binary'
            path.write_bytes(b'\x00\xff\r\n')
            self.assertEqual(p.sha256(path), p.hashlib.sha256(path.read_bytes()).hexdigest())

    def test_restore_rejects_injected_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            path.write_text(p.json.dumps({'build': p.BUILD, 'hardware': p.HARDWARE,
                'packages': {'bad; touch /sdcard/x': {'disabled_by_tool': True, 'was_disabled': False}}}))
            class Fake:
                def guard(self): pass
                def shell(self, command): raise AssertionError('Must not execute injected commands')
            with self.assertRaises(RuntimeError):
                p.restore(Fake(), path)

    def test_short_binary_backup_is_rejected(self):
        class Fake:
            def guard(self): pass
            def adb(self, *args, **kwargs):
                return p.subprocess.CompletedProcess(args, 0, stdout=b'ANDROID!')
        data = {'partitions': {'boot_a': {'start_sector': 1, 'sectors': 2},
                               'boot_b': {'start_sector': 3, 'sectors': 2}}}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'backup'
            with patch.object(p, 'inventory', return_value=data):
                with self.assertRaisesRegex(RuntimeError, 'Short backup chunk'):
                    p.backup(Fake(), target)
            self.assertFalse((target / 'manifest.json').exists())

    def test_restore_preserves_previously_disabled_packages(self):
        calls = []
        class Fake:
            def guard(self): pass
            def shell(self, command):
                calls.append(command)
                return ''
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            state.write_text(p.json.dumps({'build': p.BUILD, 'hardware': p.HARDWARE,
                'packages': {
                    p.PACKAGES[0]: {'was_disabled': True, 'disabled_by_tool': False},
                    p.PACKAGES[1]: {'was_disabled': False, 'disabled_by_tool': True}}}))
            p.restore(Fake(), state)
        self.assertNotIn('pm enable --user 0 ' + p.PACKAGES[0], calls)
        self.assertIn('pm enable --user 0 ' + p.PACKAGES[1], calls)

    def test_usb_restart_retries_stale_transport(self):
        class Fake:
            reads = 0
            def guard(self): pass
            def shell(self, command): return ''
            def adb(self, *args, **kwargs): pass
            def prop(self, key):
                if key == 'persist.adb.tcp.port': return '-1'
                self.reads += 1
                if self.reads == 1:
                    raise p.subprocess.CalledProcessError(1, 'adb')
                return '0'
        d = Fake()
        with patch.object(p.time, 'sleep'):
            p.usb_only(d)
        self.assertEqual(d.reads, 2)


if __name__ == '__main__':
    unittest.main()
