import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'install.sh'


class InstallerTests(unittest.TestCase):
    def test_active_installation_is_protected(self):
        source = SCRIPT.read_text()
        function = re.search(
            r'^ensure_not_running\(\) \{\n.*?^\}', source,
            flags=re.MULTILINE | re.DOTALL,
        ).group()
        with tempfile.TemporaryDirectory() as directory:
            child = subprocess.Popen(
                ['python3', '-c', 'import time; time.sleep(60)'],
                cwd=directory,
            )
            try:
                result = subprocess.run(
                    ['sh', '-c', 'INSTALL_ROOT=$1\n'
                     'require_command() { command -v "$1"; }\n'
                     'fail() { echo "$*" >&2; exit 1; }\n' + function +
                     '\nensure_not_running', 'test', directory],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('installation is in use', result.stderr)
                self.assertIsNone(child.poll())
            finally:
                child.terminate()
                child.wait()

    def test_download_replaces_the_demo_asset(self):
        source = SCRIPT.read_text()
        functions = '\n'.join(
            re.search(
                rf'^{name}\(\) \{{\n.*?^\}}', source,
                flags=re.MULTILINE | re.DOTALL,
            ).group()
            for name in ('download', 'install_asset')
        )
        payload = b'new verified video content'
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / 'fixture'
            fixture.write_bytes(payload)
            destination = root / 'install/hd/assets/videos/test.mp4'
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b'old static sample')
            (root / 'work/assets').mkdir(parents=True)
            shell = '''
set -eu
INSTALL_ROOT=$1/install
WORK_DIR=$1/work
FIXTURE=$1/fixture
ASSET_BASE_URL=https://example.invalid
fail() { echo "$*" >&2; exit 1; }
curl() {
    while [ "$#" -gt 0 ]; do
        if [ "$1" = --output ]; then
            cp "$FIXTURE" "$2"
            return
        fi
        shift
    done
    exit 1
}
'''
            subprocess.run(
                ['sh', '-c', shell + functions +
                 '\ninstall_asset hd "$2" media/test.mp4 '
                 'assets/videos/test.mp4', 'test', str(root), digest],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(destination.read_bytes(), payload)


if __name__ == '__main__':
    unittest.main()
