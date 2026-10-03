# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
import json
from pathlib import Path
import signal
from time import monotonic, sleep

from telemetry import SOC_TEMPERATURE, SoCTemperature


RESOURCES = ContextVar('demo_resources')
STATISTICS = ContextVar('demo_statistics', default=None)
CPU_TEMPERATURE = SoCTemperature(sensor_name='cpu-thermal')
CLOCK_SCALE = Path('/sys/bus/platform/drivers/galcore/gpu3DClockScale')


class RunStatistics:
    def __init__(self):
        self.frames = 0
        self.total_inference = 0.0
        self.first_frame = None
        self.last_frame = None
        self.soc_peak = None

    def record(self, seconds):
        now = monotonic()
        if self.first_frame is None:
            self.first_frame = now - seconds
        self.last_frame = now
        self.frames += 1
        self.total_inference += seconds
        value = SOC_TEMPERATURE.read()
        if value is not None:
            self.soc_peak = max(value, self.soc_peak or value)

    def summary(self):
        elapsed = (self.last_frame - self.first_frame
                   if self.frames else 0)
        return {
            'frames': self.frames,
            'processing_fps': (self.frames / elapsed
                               if self.frames > 1 and elapsed > 0 else None),
            'inference_ms': (1000 * self.total_inference / self.frames
                             if self.frames else None),
            'soc_peak_c': self.soc_peak,
        }


def record_inference(seconds):
    statistics = STATISTICS.get()
    if statistics is not None:
        statistics.record(seconds)


def clock_is_limited():
    try:
        return int(CLOCK_SCALE.read_text()) == 1
    except (OSError, ValueError):
        return False


def temperature():
    values = [SOC_TEMPERATURE.read(), CPU_TEMPERATURE.read()]
    return max((value for value in values if value is not None), default=None)


def register_cleanup(callback, *args):
    RESOURCES.get().callback(callback, *args)


@contextmanager
def demo_session():
    import cv2

    def terminate(_signal, _frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, terminate)
    statistics = RunStatistics()
    stats_token = STATISTICS.set(statistics)
    try:
        with ExitStack() as resources:
            token = RESOURCES.set(resources)
            resources.callback(cv2.destroyAllWindows)
            try:
                if clock_is_limited():
                    raise RuntimeError(
                        'GPU/NPU is thermally limited. Let the board cool '
                        'before restarting the demo; check heatsink and fan.'
                    )
                yield
            except KeyboardInterrupt:
                pass
            finally:
                RESOURCES.reset(token)
    finally:
        STATISTICS.reset(stats_token)
        print('VAR_AI_STATS ' + json.dumps(statistics.summary()), flush=True)
        signal.signal(signal.SIGTERM, previous)


def managed_capture(source):
    import cv2

    backend = (
        cv2.CAP_GSTREAMER if isinstance(source, str) and ' ! ' in source
        else cv2.CAP_ANY
    )
    capture = cv2.VideoCapture(source, backend, [
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000,
    ])
    register_cleanup(capture.release)
    if not capture.isOpened():
        raise RuntimeError('Cannot open the requested camera or video stream')
    return capture


class ThermalPacer:
    """Bound continuous load and cool before the kernel's 85 C trip point."""

    def __init__(self):
        self.last_frame = monotonic()
        self.cooling = False
        self.warm = False
        self.next_check = 0
        self.limited = False

    def wait(self, poll_stop=lambda: False):
        while True:
            now = monotonic()
            if now >= self.next_check:
                self.limited = clock_is_limited()
                self.next_check = now + 1
            value = temperature()
            if value is not None:
                if value >= 80:
                    self.warm = True
                elif value < 78:
                    self.warm = False
            if self.limited or (value is not None and value >= 82):
                if not self.cooling:
                    print('Cooling: inference paused until below 78 C.',
                          flush=True)
                self.cooling = True
            if self.cooling:
                if not self.limited and value is not None and value < 78:
                    self.cooling = False
                    print('Cooling complete: inference resumed.', flush=True)
                else:
                    if poll_stop():
                        return False
                    sleep(0.1)
                    continue
            rate = 15 if self.warm else 30
            remaining = 1 / rate - (now - self.last_frame)
            if remaining > 0:
                sleep(remaining)
            self.last_frame = monotonic()
            return not poll_stop()
