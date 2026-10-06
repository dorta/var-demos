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
    def test_statistics_use_invoke_time_not_process_duration(self):
        stats = runtime.RunStatistics()
        with patch.object(runtime, 'monotonic', side_effect=[1.0, 1.1]), \
                patch.object(runtime.SOC_TEMPERATURE, 'read',
                             side_effect=[70, 72]):
            stats.record(0.01)
            stats.record(0.02)
        summary = stats.summary()
        self.assertEqual(summary['frames'], 2)
        self.assertAlmostEqual(summary['inference_ms'], 15)
        self.assertAlmostEqual(summary['processing_fps'], 2 / 0.11)
        self.assertEqual(summary['soc_peak_c'], 72)

    def test_empty_statistics_do_not_invent_metrics(self):
        summary = runtime.RunStatistics().summary()
        self.assertEqual(summary['frames'], 0)
        self.assertIsNone(summary['inference_ms'])
        self.assertIsNone(summary['processing_fps'])

    def test_startup_waits_for_real_ready_event(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'startup.log'
            path.write_text('VAR_DEMO_STARTUP {"message":"Warming up",'
                            '"ready":false}\n')
            progress = runtime.StartupProgress(expected=True)
            progress.read(path)
            self.assertEqual(progress.message, 'Warming up')
            self.assertFalse(progress.ready)
            with path.open('a') as log:
                log.write('VAR_DEMO_STARTUP {"message":"First frame",'
                          '"ready":true}\n')
            progress.read(path)
            self.assertTrue(progress.ready)
            self.assertEqual(progress.message, 'First frame')

    def test_partial_or_invalid_startup_event_cannot_mark_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'startup.log'
            path.write_text('VAR_DEMO_STARTUP {broken}\n'
                            'VAR_DEMO_STARTUP {"message":"bad",'
                            '"ready":"yes"}\n'
                            'VAR_DEMO_STARTUP {"message":"Ready",')
            progress = runtime.StartupProgress(expected=True)
            progress.read(path)
            self.assertFalse(progress.ready)
            with path.open('a') as log:
                log.write('"ready":true}\n')
            progress.read(path)
            self.assertTrue(progress.ready)

    def test_mx95_cpu_sensor_participates_in_thermal_protection(self):
        with patch.object(runtime.SOC_TEMPERATURE, 'read', return_value=None), \
                patch.object(runtime.CPU_TEMPERATURE, 'read', return_value=None), \
                patch.object(runtime.A55_TEMPERATURE, 'read', return_value=83):
            self.assertEqual(runtime.temperature(), 83)

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
            CAP_ANY=0, CAP_GSTREAMER=1800,
            CAP_PROP_OPEN_TIMEOUT_MSEC=53, CAP_PROP_READ_TIMEOUT_MSEC=54,
        )
        with patch.dict(sys.modules, {'cv2': fake_cv2}):
            with patch.object(runtime, 'clock_is_limited', return_value=False):
                with self.assertRaisesRegex(RuntimeError, 'Cannot open'):
                    with runtime.demo_session():
                        runtime.managed_capture('/dev/video4')
        capture.release.assert_called_once()
        fake_cv2.VideoCapture.assert_called_once_with(
            '/dev/video4', 0, [53, 5000, 54, 2000]
        )

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
