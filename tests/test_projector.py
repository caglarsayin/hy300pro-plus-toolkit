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


if __name__ == '__main__':
    unittest.main()
