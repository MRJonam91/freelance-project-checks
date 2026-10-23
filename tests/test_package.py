"""Source package must be self-contained and leave private output behind."""
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ManojRollo
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_package_contains_license_one_calculator_and_can_run_standalone(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.test-') as directory:
            target = Path(directory) / 'source.zip'
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/package.py'), '--output', str(target)],
                capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['sha256'], hashlib.sha256(target.read_bytes()).hexdigest())
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
                base = 'freelance-project-checks-0.1.0/'
                self.assertIn(base + 'LICENSE', names)
                self.assertIn(b'GNU GENERAL PUBLIC LICENSE', archive.read(base + 'LICENSE'))
                self.assertIn(base + 'NOTICE', names)
                self.assertIn(base + 'THIRD_PARTY_NOTICES.md', names)
                self.assertEqual(len([n for n in names if n.endswith('/calculate.py')]), 1)
                self.assertFalse(any('/.work/' in n or '/products/' in n or '/.git/' in n or '/dist/' in n for n in names))
                archive.extractall(Path(directory) / 'extracted')
            extracted = Path(directory) / 'extracted' / base
            run = subprocess.run(
                [sys.executable, '-B', str(extracted / 'skills/revision-cost-check/scripts/calculate.py'),
                 str(extracted / 'skills/revision-cost-check/examples/project.json'), '--json'],
                cwd=directory, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['rows'][1]['effective_hourly'], '40.00 EUR/h')


if __name__ == '__main__':
    unittest.main(verbosity=2)
