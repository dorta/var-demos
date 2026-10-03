# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause
# Hardware integration test: opens a temporary window on the board display.

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'video-player'))
from player import GLib, Gst, Gtk, Player

if not Gtk.init_check()[0]:
    raise SystemExit('Board display unavailable')
player = Player(sys.argv[1])
errors = []


def verify(function):
    def callback():
        try:
            function()
        except Exception as error:
            errors.append(str(error))
            player.destroy()
        return False
    return callback


def pause():
    assert player.frames > 5, 'No decoded video frames reached the display'
    assert player.full, 'Player did not enter fullscreen'
    player.set_playing(False)


def resume():
    assert player.pipeline.get_state(Gst.SECOND)[1] == Gst.State.PAUSED
    player.seek(5)
    player.set_playing(True)
    player.toggle_fullscreen()


def stop():
    assert player.playing
    assert not player.full, 'Player did not leave fullscreen'
    player.toggle_fullscreen()
    player.stop()
    assert player.pipeline.get_state(Gst.SECOND)[1] == Gst.State.READY
    assert not player.progress.get_sensitive()
    player.set_playing(True)


GLib.timeout_add_seconds(2, verify(pause))
GLib.timeout_add_seconds(4, verify(resume))
GLib.timeout_add_seconds(7, verify(stop))
def close():
    assert player.full, 'Player did not re-enter fullscreen'
    player.destroy()


GLib.timeout_add_seconds(10, verify(close))
Gtk.main()
assert player.pipeline.get_state(Gst.SECOND)[1] == Gst.State.NULL
if errors:
    raise SystemExit('; '.join(errors))
print(f'PASS: play, pause, seek, stop, restart, close; {player.frames} frames')
