import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
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
        self.assertIn('Chicago', video['title'])

    def test_back_does_not_launch_a_video(self):
        with patch('builtins.input', return_value='b'):
            with patch('builtins.print'):
                self.assertIsNone(manager.select_video(
                    self.catalog, self.launcher['demo']
                ))

    def test_selected_video_controls_input_and_resolution(self):
        video = self.catalog['videos'][-1]
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
