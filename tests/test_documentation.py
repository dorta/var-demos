from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUIDES = ['README.md', 'ai-ml-demos/README.adoc',
          'ai-ml-demos/classification/README.adoc',
          'ai-ml-demos/detection/README.adoc',
          'ai-ml-demos/high-resolution-video-detection/README.md',
          'ai-ml-demos/hand-gesture/README.md',
          'multimedia-demos/README.md', 'opencl/python/README.md',
          'ai-ml-demos/camera-vision/README.md']
GUIDES += [str(path.relative_to(ROOT)) for path in sorted((ROOT / 'docs').rglob('*.md'))]


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
                    self.assertTrue((path.parent / target.split('#', 1)[0]).exists())
                    if '#' in target:
                        file_target, anchor = target.split('#', 1)
                        contents = (path.parent / file_target).read_text()
                        headings = re.findall(r'^#{1,6}\s+(.+)$', contents, re.M)
                        anchors = {re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
                                   for heading in headings}
                        self.assertIn(anchor, anchors)

    def test_each_npu_has_libraries_startup_and_task_flows(self):
        for name in ('vip8000', 'ethos-u65', 'neutron'):
            text = (ROOT / 'docs/npus' / (name + '.md')).read_text()
            for heading in ('NPU and Libraries', 'Starting a Demo',
                            'Classification Flow', 'Detection Flow',
                            'Hardware Versus Software'):
                self.assertRegex(text, r'#{2,3} ' + heading)
            self.assertEqual(text.count('```mermaid'), 2)
            self.assertIn('https://www.nxp.com/docs/en/user-guide/UG10166.pdf', text)

    def test_root_guide_keeps_install_and_run_concise(self):
        text = (ROOT / 'README.md').read_text()
        self.assertNotIn('—', text)
        self.assertNotIn('–', text)
        self.assertLess(len(text.splitlines()), 80)
        self.assertIn('## Installing Variscite Demos', text)
        self.assertIn('## Running Variscite Demos', text)
        self.assertIn('## Documentation', text)
        self.assertIn('curl -fsSL https://raw.githubusercontent.com/'
                      'dorta/var-demos/demos/install.sh | sh', text)
        self.assertIn('```sh\nvar-demos\n```', text)
        self.assertNotIn('## Manage', text)
        self.assertIn('alt="Variscite" width="320"', text)
        self.assertIn('## Supported System on Modules', text)
        for guide in ('som-support', 'models', 'model-conversion',
                      'video-sources', 'performance', 'validation'):
            self.assertIn('(docs/' + guide + '.md)', text)

    def test_model_flows_and_details_are_preserved_in_docs(self):
        text = (ROOT / 'docs/models.md').read_text()
        self.assertIn('| Model Detail | i.MX 8M Plus | VAR-SOM-MX93 | DART-MX95 |', text)
        self.assertEqual(text.count('```mermaid'), 3)
        for heading in ('Model Preparation Flow', 'Classification Flow', 'Detection Flow'):
            self.assertIn('### ' + heading, text)

    def test_internal_documentation_links_are_not_repository_specific(self):
        for filename in GUIDES:
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                self.assertNotRegex(text, r'https://github\.com/dorta/var-demos(?:/|\b)')

    def test_performance_tables_have_identical_scenarios_and_columns(self):
        performance = (ROOT / 'docs/performance.md').read_text()
        expected = ['Image classification', 'Image detection',
                    '720p video classification', '1080p video classification',
                    'Camera classification', 'Camera detection',
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
                    self.assertEqual(cells[3:], ['N/A', 'N/A', 'N/A'])
        self.assertIn('not one standardized benchmark', performance)


if __name__ == '__main__':
    unittest.main()
