#!/usr/bin/env python3
"""Query Allwinner 1f3a:1010 using PyUSB. No flash/unlock/download commands."""
import argparse
import time
import usb.core
import usb.util
import usb.backend.libusb1

QUERIES = ('version', 'secure', 'unlocked', 'current-slot',
           'max-download-size', 'partition-size:boot_a')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.parse_args()
    backend = usb.backend.libusb1.get_backend(find_library=lambda _: '/opt/homebrew/lib/libusb-1.0.dylib')
    device = usb.core.find(idVendor=0x1f3a, idProduct=0x1010, backend=backend)
    if device is None:
        raise SystemExit('Allwinner fastboot USB device not found.')
    try:
        try:
            device.get_active_configuration()
        except usb.core.USBError:
            device.set_configuration()
        config = device.get_active_configuration()
        interfaces = [i for i in config if (i.bInterfaceClass, i.bInterfaceSubClass,
                      i.bInterfaceProtocol) == (0xff, 0x42, 3)]
        if len(interfaces) != 1:
            raise SystemExit('Expected exactly one standard fastboot interface; refusing protocol guesses.')
        interface = interfaces[0]
        usb.util.claim_interface(device, interface.bInterfaceNumber)
        endpoints = list(interface)
        out = [e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
               and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK]
        incoming = [e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                    and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK]
        if len(out) != 1 or len(incoming) != 1:
            raise SystemExit('Unexpected fastboot bulk endpoints.')
        def query(command):
            out[0].write(command.encode('ascii'), timeout=3000)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                response = bytes(incoming[0].read(512, timeout=3000)).decode('utf-8', errors='replace')
                print(command, response, flush=True)
                if response.startswith(('OKAY', 'FAIL')):
                    return
            raise RuntimeError('Fastboot response deadline exceeded')
        for name in QUERIES:
            query('getvar:' + name)
    finally:
        usb.util.dispose_resources(device)


if __name__ == '__main__':
    try:
        main()
    except (usb.core.USBError, RuntimeError) as exc:
        raise SystemExit('USB query failed; no flash was attempted: ' + str(exc))
