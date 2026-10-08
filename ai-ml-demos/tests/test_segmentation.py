# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import manager
import vision_overlay as ui
spec = importlib.util.spec_from_file_location('segmentation', ROOT / 'camera-vision/segmentation.py')
segmentation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(segmentation)


class SegmentationTests(unittest.TestCase):
    def test_tensor_view_returns_an_independent_mask_without_score_copy(self):
        scores = np.zeros((1, 2, 3, 21), np.float32)
        scores[..., 15] = 1
        interpreter = Mock()
        interpreter.tensor.return_value = lambda: scores
        mask = segmentation.read_segmentation(interpreter, dict(index=12))
        interpreter.tensor.assert_called_once_with(12)
        interpreter.get_tensor.assert_not_called()
        self.assertFalse(np.shares_memory(mask, scores))
        scores[:] = 0
        self.assertTrue((mask == 15).all())

    def test_float_boundary_normalization_and_rgb_order(self):
        image = np.array([[[0, 127, 255]]], np.uint8)
        actual = segmentation.prepare_segmentation_input(image, dict(dtype=np.float32))
        np.testing.assert_allclose(actual, [[[[-1, -1 / 255, 1]]]], atol=1e-7)
        self.assertEqual(actual.dtype, np.float32)
        with self.assertRaises(ValueError):
            segmentation.prepare_segmentation_input(image, dict(dtype=np.uint8))

    def test_per_pixel_argmax_returns_classes_not_boxes(self):
        scores = np.zeros((1, 2, 3, 21), np.float32)
        scores[0, 0, 0, 15] = 2
        scores[0, 1, 2, 7] = 3
        expected = np.array([[15, 0, 0], [0, 0, 7]], np.uint8)
        np.testing.assert_array_equal(segmentation.decode_segmentation(scores), expected)
        for invalid in (np.zeros((1, 2, 3, 20)), np.full((1, 2, 3, 21), np.nan)):
            with self.assertRaises(ValueError):
                segmentation.decode_segmentation(invalid)

    def test_only_people_and_vehicles_are_painted_inside_viewport(self):
        frame = np.full((8, 10, 3), 100, np.uint8)
        original = frame.copy()
        classes = np.array([[15, 7, 8, 0]], np.uint8)
        people, vehicles = segmentation.paint_segmentation(frame, classes, (1, 2, 8, 4))
        self.assertEqual((people, vehicles), (.25, .25))
        np.testing.assert_array_equal(frame[:2], original[:2])
        np.testing.assert_array_equal(frame[6:], original[6:])
        np.testing.assert_array_equal(frame[2:6, 5:], original[2:6, 5:])
        np.testing.assert_array_equal(frame[2, 1],
            np.rint(100 * .55 + np.array(ui.color_for('person')) * .45))
        np.testing.assert_array_equal(frame[2, 3],
            np.rint(100 * .55 + np.array(ui.color_for('car')) * .45))

    def test_zero_opacity_preserves_frame_and_invalid_opacity_is_rejected(self):
        frame = np.full((4, 4, 3), 72, np.uint8)
        original = frame.copy()
        mask = np.full((2, 2), 15, np.uint8)
        segmentation.paint_segmentation(frame, mask, (0, 0, 4, 4), opacity=0)
        np.testing.assert_array_equal(frame, original)
        with self.assertRaises(ValueError):
            segmentation.paint_segmentation(frame, mask, (0, 0, 4, 4), opacity=2)

    def test_shared_modes_follow_faces_and_keep_camera_quality_selector(self):
        catalog = manager.load_catalog()
        for platform in ('imx8mplus', 'imx93'):
            launchers = manager.launchers_for(catalog, platform)
            items = launchers[9:12]
            self.assertEqual([x['id'].removeprefix('ethosu-') for x in items],
                             ['segmentation-image', 'segmentation-video', 'segmentation-camera'])
            self.assertTrue(items[2]['select_camera'])
            video_demo = manager.launcher_video_demo(items[1], platform)
            self.assertEqual([x['id'] for x in manager.video_resolutions(catalog, video_demo)],
                             ['720p', '1080p'])
            self.assertNotIn('--windowed', items[0]['command'])
        self.assertFalse(any('segmentation' in item['id']
                             for item in manager.launchers_for(catalog, 'imx95')))
