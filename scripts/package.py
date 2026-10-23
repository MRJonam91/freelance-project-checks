"""Build an allowlisted source ZIP and SHA-256 file using the standard library."""
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ManojRollo
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    '.gitignore', '.github/FUNDING.yml', '.github/workflows/tests.yml',
    'README.md', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'ASSETS.md',
    'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'SECURITY.md', 'SUPPORT.md',
    'CHANGELOG.md', 'VERSION', 'scripts/package.py',
    'tests/test_calculator.py', 'tests/test_package.py',
    'skills/revision-cost-check/SKILL.md',
    'skills/revision-cost-check/scripts/calculate.py',
    'skills/revision-cost-check/references/input.md',
    'skills/revision-cost-check/examples/project.json',
    'skills/revision-cost-check/examples/project.md',
]


def main():
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    name = 'freelance-project-checks-' + version
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' / (name + '.zip'))
    args = parser.parse_args()
    sources = []
    for relative in sorted(FILES):
        source = ROOT / relative
        if source.is_symlink() or not source.is_file():
            parser.error('Missing or symlinked package source: ' + relative)
        sources.append((relative, source.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, content in sources:
            info = zipfile.ZipInfo(name + '/' + relative, date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compresslevel=9)
    checksum = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix + '.sha256').write_text(
        checksum + '  ' + args.output.name + '\n', encoding='utf-8')
    print(json.dumps({'version': version, 'files': len(sources), 'sha256': checksum,
                      'artifact': str(args.output.resolve())}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
