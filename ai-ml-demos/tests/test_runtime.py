import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location('runtime', ROOT / 'runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def test_cleanup_runs_when_a_demo_fails(self):
        cleanup = MagicMock()
        fake_cv2 = SimpleNamespace(destroyAllWindows=MagicMock())
        with patch.dict(sys.modules, {'cv2': fake_cv2}):
            with patch.object(runtime, 'clock_is_limited', return_value=False):
                with self.assertRaises(RuntimeError):
                    with runtime.demo_session():
                        runtime.register_cleanup(cleanup)
                        raise RuntimeError('capture failed')
        cleanup.assert_called_once()
        fake_cv2.destroyAllWindows.assert_called_once()

    def test_missing_capture_is_reported_and_released(self):
        capture = MagicMock()
        capture.isOpened.return_value = False
        fake_cv2 = SimpleNamespace(
            destroyAllWindows=MagicMock(),
            VideoCapture=MagicMock(return_value=capture),
        )
        with patch.dict(sys.modules, {'cv2': fake_cv2}):
            with patch.object(runtime, 'clock_is_limited', return_value=False):
                with self.assertRaisesRegex(RuntimeError, 'Cannot open'):
                    with runtime.demo_session():
                        runtime.managed_capture('/dev/video4')
        capture.release.assert_called_once()

    def test_thermal_trip_blocks_startup(self):
        fake_cv2 = SimpleNamespace(destroyAllWindows=MagicMock())
        with patch.dict(sys.modules, {'cv2': fake_cv2}):
            with patch.object(runtime, 'clock_is_limited', return_value=True):
                with self.assertRaisesRegex(RuntimeError, 'thermally limited'):
                    with runtime.demo_session():
                        self.fail('a throttled demo must not start')

    def test_clock_scale_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = Path(directory) / 'scale'
            with patch.object(runtime, 'CLOCK_SCALE', clock):
                self.assertFalse(runtime.clock_is_limited())
                clock.write_text('1')
                self.assertTrue(runtime.clock_is_limited())
                clock.write_text('64')
                self.assertFalse(runtime.clock_is_limited())

    def test_load_is_reduced_when_hot(self):
        with patch.object(runtime, 'monotonic', return_value=10):
            with patch.object(runtime, 'temperature', return_value=81):
                with patch.object(runtime, 'clock_is_limited', return_value=False):
                    with patch.object(runtime, 'sleep') as sleep:
                        self.assertTrue(runtime.ThermalPacer().wait())
        sleep.assert_called_once_with(1 / 15)

    def test_cooling_can_be_cancelled(self):
        with patch.object(runtime, 'temperature', return_value=83):
            with patch.object(runtime, 'clock_is_limited', return_value=False):
                with patch('builtins.print'):
                    self.assertFalse(runtime.ThermalPacer().wait(lambda: True))


if __name__ == '__main__':
    unittest.main()
