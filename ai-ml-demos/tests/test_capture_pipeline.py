# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import ast
from pathlib import Path
import unittest


# The pipeline builder is pure; load it without importing target-only TFLite.
SOURCE = Path(__file__).resolve().parents[1] / 'camera-vision/demo.py'
tree = ast.parse(SOURCE.read_text())
builder = next(node for node in tree.body
               if isinstance(node, ast.FunctionDef)
               and node.name == 'capture_tail')
namespace = {}
exec(compile(ast.Module(body=[builder], type_ignores=[]), str(SOURCE), 'exec'),
     namespace)


class CapturePipelineTests(unittest.TestCase):
    def test_live_sink_is_discoverable_by_opencv(self):
        description = namespace['capture_tail'](False)
        self.assertIn('appsink name=opencvsink ', description)
        self.assertIn('format=BGR', description)
        self.assertIn('max-buffers=1', description)

    def test_file_sink_matches_gi_reader(self):
        description = namespace['capture_tail'](True)
        self.assertIn('appsink name=frames ', description)
        self.assertNotIn('opencvsink', description)
