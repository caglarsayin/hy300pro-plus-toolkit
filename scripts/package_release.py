#!/usr/bin/env python3
"""Create a source-only archive with an explicit allowlist; never walk backups."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    '.gitignore', 'LICENSE', 'README.md',
    'docs/FINDINGS.md', 'docs/ROOT-AND-RECOVERY.md', 'docs/SOURCES.md',
    'scripts/projector.py', 'scripts/patch_boot.py', 'scripts/package_release.py',
    'scripts/fastboot_probe.py',
    'tests/test_projector.py',
)


def main():
    out = ROOT.parent / 'hy300pro-plus-toolkit-source.zip'
    manifest = {}
    for name in FILES:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise SystemExit('Missing/nonregular release source: ' + name)
        manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(ROOT / name, 'hy300pro-plus-toolkit/' + name)
        z.writestr('hy300pro-plus-toolkit/SHA256SUMS.json', json.dumps(manifest, indent=2) + '\n')
    print(out)
    print('SHA256', hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
