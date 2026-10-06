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

    def test_root_guide_keeps_install_and_run_concise(self):
        text = (ROOT / 'README.md').read_text()
        self.assertIn('curl -fsSL https://raw.githubusercontent.com/'
                      'dorta/var-demos/demos/install.sh | sh', text)
        self.assertIn('```sh\nvar-demos\n```', text)
        self.assertNotIn('## Manage', text)
        self.assertIn('alt="Variscite" width="320"', text)
        for board in ('i.MX 8M Plus', 'VAR-SOM-MX93', 'DART-MX95'):
            self.assertIn('### ' + board, text)

    def test_performance_tables_have_identical_scenarios_and_columns(self):
        text = (ROOT / 'README.md').read_text()
        performance = text.split('## Performance\n', 1)[1]
        expected = ['Camera classification', 'Camera detection',
                    '720p video detection', '1080p video detection',
                    'Video player', 'OpenCL / GPU examples', 'Hand gestures']
        for section in performance.split('### ')[1:]:
            rows = [line for line in section.splitlines()
                    if line.startswith('|')]
            self.assertEqual(rows[0], '| Scenario | Source | Validation | '
                             'Duration | FPS | Inference |')
            self.assertEqual([row.split('|')[1].strip() for row in rows[2:]],
                             expected)
            for row in rows[2:]:
                cells = [cell.strip() for cell in row.split('|')[1:-1]]
                self.assertIn(cells[2], ('Measured', 'Functional',
                                        'Experimental', 'Not enabled'))
                if cells[2] != 'Measured':
                    self.assertEqual(cells[3:], ['—', '—', '—'])
        self.assertIn('not one standardized benchmark', performance)


if __name__ == '__main__':
    unittest.main()
