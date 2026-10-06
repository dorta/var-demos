from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUIDES = ['README.md', 'CONVERTING_MODELS.md', 'ai-ml-demos/README.adoc',
          'ai-ml-demos/classification/README.adoc',
          'ai-ml-demos/detection/README.adoc',
          'ai-ml-demos/high-resolution-video-detection/README.md',
          'ai-ml-demos/hand-gesture/README.md',
          'multimedia-demos/README.md', 'opencl/python/README.md']


class DocumentationTests(unittest.TestCase):
    def test_current_guides_do_not_use_obsolete_launchers_or_paths(self):
        stale = r'\bvar-ai\b|\bvar-media\b|tflite/classification|tflite/detection'
        for filename in GUIDES:
            with self.subTest(filename=filename):
                self.assertIsNone(re.search(stale, (ROOT / filename).read_text()))

    def test_relative_readme_links_resolve(self):
        for filename in GUIDES:
            path = ROOT / filename
            text = path.read_text()
            links = re.findall(r'\]\(([^)]+)\)', text)
            links.extend(re.findall(r'link:([^\[]+)\[', text))
            for target in links:
                if '://' in target or target.startswith('#'):
                    continue
                with self.subTest(filename=filename, target=target):
                    self.assertTrue((path.parent / target).exists())

    def test_root_guide_uses_unified_management_commands(self):
        text = (ROOT / 'README.md').read_text()
        for command in ('var-demos status', 'var-demos --list',
                        'var-demos --uninstall'):
            self.assertIn(command, text)


if __name__ == '__main__':
    unittest.main()
