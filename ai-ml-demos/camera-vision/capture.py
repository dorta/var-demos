# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo

Gst.init(None)


class VideoCapture:
    """Own each BGR frame and distinguish actual EOS from a pipeline failure."""

    def __init__(self, description):
        self.pipeline = Gst.parse_launch(description)
        self.sink = self.pipeline.get_by_name('frames')
        self.bus = self.pipeline.get_bus()
        self.closed = False
        self.last_pts = None
        if self.pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            self.release()
            raise RuntimeError('Could not start the video pipeline')

    def read(self):
        sample = self.sink.emit('try-pull-sample', 2 * Gst.SECOND)
        if sample is None:
            message = self.bus.pop_filtered(Gst.MessageType.ERROR |
                                            Gst.MessageType.EOS)
            if message and message.type == Gst.MessageType.ERROR:
                error, debug = message.parse_error()
                raise RuntimeError(f'Video pipeline failed: {error}: {debug}')
            if self.sink.get_property('eos'):
                return False, None
            raise RuntimeError('Video pipeline timed out before end of stream')
        info = GstVideo.VideoInfo.new_from_caps(sample.get_caps())
        if info.finfo.name != 'BGR':
            raise RuntimeError(f'Expected BGR, received {info.finfo.name}')
        buffer = sample.get_buffer()
        self.last_pts = buffer.pts
        pixels = buffer.extract_dup(0, buffer.get_size())
        rows = np.frombuffer(pixels, np.uint8).reshape(info.height, info.stride[0])
        return True, rows[:, :info.width * 3].reshape(
            info.height, info.width, 3).copy()

    def release(self):
        if not self.closed:
            self.closed = True
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline.get_state(2 * Gst.SECOND)
