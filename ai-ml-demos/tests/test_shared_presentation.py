import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import manager
import vision_overlay as ui


class SharedPresentationTests(unittest.TestCase):
    def test_panel_background_is_cached_without_mutating_the_color(self):
        bg = ui.panel_background((10, 20, 3), False)
        self.assertIs(bg, ui.panel_background((10, 20, 3), False))
        self.assertFalse(bg.flags.writeable)
        frame = np.full((30, 40, 3), 180, np.uint8)
        ui.panel(frame, 0, 0, 20, 10)
        np.testing.assert_array_equal(bg[0, 0], ui.PANEL)
        np.testing.assert_array_equal(ui.panel_background((10, 20, 3), True)[0, 0],
                                      ui.PANEL[::-1])

    def test_shared_demos_first_in_identical_order(self):
        catalog = manager.load_catalog()
        expected = ['classification-image', 'classification-video',
                    'classification-camera', 'detection-image',
                    'detection-video', 'detection-camera']
        for board in catalog['platforms']:
            launchers = manager.launchers_for(catalog, board)
            ids = [x['id'].removeprefix('ethosu-').removeprefix('neutron-')
                   for x in launchers[:6]]
            self.assertEqual(ids, expected, board)
            self.assertTrue(all('--windowed' not in x['command']
                                for x in launchers))

    def test_video_menus_identical_and_assets_present_in_manifests(self):
        catalog = manager.load_catalog()
        titles = []
        root = Path(__file__).resolve().parents[1]
        for demo_id in ['high-resolution-video-detection', 'vision-imx93', 'vision-imx95']:
            videos = [x for x in catalog['videos'] if x['demo'] == demo_id]
            self.assertEqual(len(videos), 8)
            titles.append([x['title'] for x in videos])
            demo = manager.find_demo(catalog, demo_id)
            assets = (root / demo['path'] / demo['manifest']).read_text()
            self.assertTrue(all(x['path'] in assets for x in videos))
        self.assertEqual(titles[0], titles[1])
        self.assertEqual(titles[1], titles[2])

    def test_camera_resolution_does_not_mutate_catalog_command(self):
        catalog = manager.load_catalog()
        for board in catalog['platforms']:
            for item in manager.launchers_for(catalog, board):
                if not item.get('select_camera'):
                    continue
                selected = manager.with_camera_resolution(item,
                    manager.camera_choices(catalog, board)[0])
                self.assertEqual(selected['command'][-2], '--resolution')
                self.assertNotIn('--resolution', item['command'])

    def test_badge_origin_does_not_change_with_values(self):
        frame = np.zeros((480, 800, 3), np.uint8)
        with patch.object(ui, 'panel') as panel:
            ui.statistics(frame, 1.2, 9.9)
            first = panel.call_args_list
            panel.reset_mock()
            ui.statistics(frame, 123.4, 100.0)
            self.assertEqual(first, panel.call_args_list)

    def test_semantic_colors_independent_of_class_index(self):
        self.assertEqual(ui.color_for(' person '), ui.PALETTE[0])
        self.assertEqual(ui.color_for('CAR'), ui.PALETTE[2])
        self.assertEqual(ui.color_for('car', True), ui.color_for('car')[::-1])

    def test_rgb_and_bgr_paths_have_same_colors(self):
        bgr = np.zeros((480, 800, 3), np.uint8)
        rgb = bgr.copy()
        for frame, is_rgb in [(bgr, False), (rgb, True)]:
            ui.statistics(frame, 12.3, 25, is_rgb)
            ui.model(frame, 'SSD | NPU', is_rgb)
            ui.temperature(frame, 81.2, is_rgb)
            ui.results(frame, [('person', .95)], is_rgb)
            ui.box(frame, (200, 150, 400, 300), 'car', .8, is_rgb)
        np.testing.assert_array_equal(bgr, rgb[:, :, ::-1])
