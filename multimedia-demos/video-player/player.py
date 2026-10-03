#!/usr/bin/env python3
# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import os
from pathlib import Path
import signal
import sys

runtime = Path(os.environ.setdefault('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
if not os.environ.get('WAYLAND_DISPLAY'):
    sockets = sorted(path for path in runtime.glob('wayland-*') if path.is_socket())
    if sockets:
        os.environ['WAYLAND_DISPLAY'] = sockets[0].name

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
    gi.require_version('Gst', '1.0')
    gi.require_version('GstVideo', '1.0')
    from gi.repository import Gdk, GdkPixbuf, GLib, Gst, GstVideo, Gtk
except (ImportError, ValueError) as error:
    raise SystemExit(f'GTK 3 / GStreamer Python bindings required: {error}')

Gst.init(None)


def clock_text(seconds):
    seconds = max(0, int(seconds))
    return f'{seconds // 60:02d}:{seconds % 60:02d}'


def check_runtime():
    for name in ('playbin', 'appsink', 'videoconvert', 'videoscale'):
        if Gst.ElementFactory.find(name) is None:
            raise RuntimeError(f'Missing GStreamer element: {name}')


class Player(Gtk.Window):
    def __init__(self, filename=None, windowed=False):
        super().__init__(title='Variscite video player')
        self.set_default_size(800, 480)
        self.connect('destroy', self.shutdown)
        self.connect('key-press-event', self.on_key)
        self.uri = None
        self.playing = False
        self.finished = False
        self.seeking = False
        self.full = not windowed
        self.frames = 0
        self.tick_id = None
        self.closed = False
        self.pipeline = Gst.ElementFactory.make('playbin', 'player')
        # Bounded preview frames keep Python memory stable. GStreamer chooses
        # the available decoder; the UI does not claim hardware acceleration.
        sink_bin = Gst.parse_bin_from_description(
            'videoconvert ! videoscale add-borders=true ! '
            'video/x-raw,format=RGB,width=640,height=336,'
            'pixel-aspect-ratio=1/1 ! appsink name=preview '
            'max-buffers=1 drop=true sync=true wait-on-eos=false', True
        )
        self.sink = sink_bin.get_by_name('preview')
        self.pipeline.set_property('video-sink', sink_bin)
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus_id = self.bus.connect('message', self.on_message)

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        layout.set_border_width(8)
        self.add(layout)
        header = Gtk.Box(spacing=8)
        layout.pack_start(header, False, False, 0)
        title = Gtk.Label(label='VARISCITE  /  VIDEO PLAYER')
        header.pack_start(title, False, False, 0)
        self.filename = Gtk.Label(label='Open a local movie')
        self.filename.set_ellipsize(3)
        header.pack_start(self.filename, True, True, 0)
        self.button(header, 'Open', self.choose_file)
        self.button(header, 'Exit', lambda _: self.destroy())
        self.image = Gtk.Image()
        layout.pack_start(self.image, True, True, 0)

        timeline = Gtk.Box(spacing=8)
        layout.pack_start(timeline, False, False, 0)
        self.progress = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 0.1
        )
        self.progress.set_draw_value(False)
        self.progress.connect('button-press-event', self.begin_seek)
        self.progress.connect('button-release-event', self.end_seek)
        self.progress.connect('change-value', self.change_seek)
        self.progress.set_sensitive(False)
        timeline.pack_start(self.progress, True, True, 0)
        self.time_label = Gtk.Label(label='00:00 / 00:00')
        timeline.pack_start(self.time_label, False, False, 0)
        controls = Gtk.Box(spacing=8)
        layout.pack_start(controls, False, False, 0)
        self.play_button = self.button(controls, 'Play', self.toggle_play)
        self.button(controls, 'Stop', self.stop)
        self.button(controls, 'Fullscreen', self.toggle_fullscreen)
        controls.pack_start(Gtk.Label(label='Volume'), False, False, 0)
        volume = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, .05)
        volume.set_size_request(110, -1)
        volume.set_value(.7)
        volume.set_draw_value(False)
        volume.connect('value-changed', lambda scale:
                       self.pipeline.set_property('volume', scale.get_value()))
        self.pipeline.set_property('volume', .7)
        controls.pack_start(volume, False, False, 0)
        self.status = Gtk.Label(label='Space: play/pause  |  Esc: exit')
        controls.pack_start(self.status, True, True, 0)
        self.show_all()
        if self.full:
            self.fullscreen()
        self.tick_id = GLib.timeout_add(33, self.tick)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM,
                             self.signal_quit)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,
                             self.signal_quit)
        if filename:
            GLib.idle_add(self.open_file, filename)

    def button(self, parent, label, callback):
        button = Gtk.Button(label=label)
        button.connect('clicked', callback)
        parent.pack_start(button, False, False, 0)
        return button

    def choose_file(self, _):
        dialog = Gtk.FileChooserDialog(
            title='Open a movie', parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons('Cancel', Gtk.ResponseType.CANCEL,
                           'Open', Gtk.ResponseType.OK)
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Movies')
        file_filter.add_mime_type('video/*')
        dialog.add_filter(file_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            self.open_file(filename)
        else:
            dialog.destroy()

    def open_file(self, filename):
        path = Path(filename).expanduser().resolve()
        if not path.is_file():
            self.status.set_text('File not found')
            return False
        self.pipeline.set_state(Gst.State.NULL)
        self.uri = path.as_uri()
        self.filename.set_text(path.name)
        self.pipeline.set_property('uri', self.uri)
        self.frames = 0
        self.finished = False
        self.set_playing(True)
        return False

    def set_playing(self, playing):
        if not self.uri:
            self.status.set_text('Open a movie first')
            return
        if self.finished:
            self.pipeline.seek_simple(Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)
            self.finished = False
        state = Gst.State.PLAYING if playing else Gst.State.PAUSED
        if self.pipeline.set_state(state) == Gst.StateChangeReturn.FAILURE:
            self.status.set_text('Cannot start playback; inspect diagnostic log')
            return
        self.playing = playing
        self.play_button.set_label('Pause' if playing else 'Play')
        self.status.set_text('Playing' if playing else 'Paused')

    def toggle_play(self, _=None):
        self.set_playing(not self.playing)

    def stop(self, _=None):
        self.pipeline.set_state(Gst.State.READY)
        self.playing = False
        self.finished = False
        self.play_button.set_label('Play')
        self.progress.set_value(0)
        self.progress.set_sensitive(False)
        self.time_label.set_text('00:00 / 00:00')
        self.image.clear()
        self.status.set_text('Stopped')

    def begin_seek(self, *_):
        self.seeking = True
        return False

    def end_seek(self, *_):
        self.seek(self.progress.get_value())
        self.seeking = False
        return False

    def change_seek(self, _scale, _scroll, value):
        if not self.seeking:
            self.seek(value)
        return False

    def seek(self, seconds):
        if not self.pipeline.seek_simple(Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            int(max(0, seconds) * Gst.SECOND)):
            self.status.set_text('This stream does not support seeking')

    def toggle_fullscreen(self, _=None):
        self.full = not self.full
        self.fullscreen() if self.full else self.unfullscreen()

    def on_key(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
        elif event.keyval == Gdk.KEY_space:
            self.toggle_play()
        elif event.keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.toggle_fullscreen()
        elif event.keyval in (Gdk.KEY_s, Gdk.KEY_S):
            self.stop()
        else:
            return False
        return True

    def on_message(self, _bus, message):
        if message.type == Gst.MessageType.ERROR:
            error, debug = message.parse_error()
            print(f'Playback error: {error}\n{debug}', file=sys.stderr, flush=True)
            self.stop()
            self.status.set_text('Playback failed; open another movie')
        elif message.type == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.playing = False
            self.finished = True
            self.play_button.set_label('Replay')
            self.status.set_text('Finished')
            print(f'Playback finished; displayed {self.frames} frames.', flush=True)

    def tick(self):
        sample = self.sink.emit('try-pull-sample', 0)
        if sample:
            info = GstVideo.VideoInfo.new_from_caps(sample.get_caps())
            buffer = sample.get_buffer()
            data = GLib.Bytes.new(buffer.extract_dup(0, buffer.get_size()))
            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                data, GdkPixbuf.Colorspace.RGB, False, 8,
                info.width, info.height, info.stride[0]
            )
            self.image.set_from_pixbuf(pixbuf)
            self.frames += 1
        if not self.seeking:
            got_duration, duration = self.pipeline.query_duration(Gst.Format.TIME)
            got_position, position = self.pipeline.query_position(Gst.Format.TIME)
            if got_duration and duration > 0 and got_position:
                self.progress.set_sensitive(True)
                self.progress.set_range(0, duration / Gst.SECOND)
                self.progress.set_value(position / Gst.SECOND)
                self.time_label.set_text(
                    f'{clock_text(position / Gst.SECOND)} / '
                    f'{clock_text(duration / Gst.SECOND)}'
                )
        return not self.closed

    def signal_quit(self):
        self.destroy()
        return GLib.SOURCE_REMOVE

    def shutdown(self, *_):
        if self.closed:
            return
        self.closed = True
        if self.tick_id is not None:
            GLib.source_remove(self.tick_id)
        self.pipeline.set_state(Gst.State.NULL)
        self.bus.disconnect(self.bus_id)
        self.bus.remove_signal_watch()
        Gtk.main_quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('movie', nargs='?')
    parser.add_argument('--windowed', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    check_runtime()
    if args.check:
        print('GTK 3 and GStreamer player dependencies available')
        return
    if not Gtk.init_check()[0]:
        raise SystemExit('Cannot connect to the board display')
    sample = Path(__file__).with_name('media') / 'chicago.mp4'
    filename = args.movie or (str(sample) if sample.is_file() else None)
    Player(filename, args.windowed)
    Gtk.main()


if __name__ == '__main__':
    main()
