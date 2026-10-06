import importlib.util
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location('manager', ROOT / 'manager.py')
manager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manager)


class VideoMenuTests(unittest.TestCase):
    def setUp(self):
        self.catalog = manager.load_catalog()
        self.launcher = next(
            item for item in self.catalog['launchers']
            if item['id'] == 'detection-hd-video'
        )

    def test_invalid_choices_do_not_select_a_video(self):
        with patch('builtins.input', side_effect=['0', '-1', 'oops', '1']):
            with patch('builtins.print'):
                video = manager.select_video(
                    self.catalog, self.launcher['demo']
                )
        self.assertIn('High-rise buildings A', video['title'])

    def test_back_does_not_launch_a_video(self):
        with patch('builtins.input', return_value='b'):
            with patch('builtins.print'):
                self.assertIsNone(manager.select_video(
                    self.catalog, self.launcher['demo']
                ))

    def test_both_buildings_clips_have_hd_and_full_hd_on_each_board(self):
        manifests = {
            'high-resolution-video-detection':
                'high-resolution-video-detection/assets.manifest',
            'vision-imx93': 'camera-vision/assets-imx93.manifest',
            'vision-imx95': 'camera-vision/assets-imx95.manifest',
        }
        for demo, manifest in manifests.items():
            assets = {line.split()[2] for line in
                      (ROOT / manifest).read_text().splitlines()
                      if line and not line.startswith('#')}
            videos = [item for item in self.catalog['videos']
                      if item['demo'] == demo]
            self.assertIn('1280x720', videos[0]['path'])
            for clip in ('458687', '458688'):
                for resolution in ('1280x720', '1920x1080'):
                    matches = [item for item in videos
                               if clip in item['path']
                               and resolution in item['path']]
                    self.assertEqual(len(matches), 1)
                    self.assertIn(matches[0]['path'], assets)

    def test_selected_video_controls_input_and_resolution(self):
        video = [item for item in self.catalog['videos']
                 if item['demo'] == self.launcher['demo']][-1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / self.launcher['demo'] / video['path']
            path.parent.mkdir(parents=True)
            path.touch()
            with patch.object(manager, 'ROOT', root):
                with patch.object(manager.subprocess, 'run') as run:
                    manager.run_launcher(
                        self.catalog, self.launcher,
                        dashboard=False, video=video,
                    )
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ['--video', str(path)])
            self.assertEqual(
                command[command.index('--combination') + 1], '14'
            )


if __name__ == '__main__':
    unittest.main()
