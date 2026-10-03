# Multimedia demos

Launch the video player from `var-demos`, or run `var-media` directly.

Open a local movie. Use Play/Pause, Stop, the seek bar and volume slider.
Space toggles playback; S stops; F toggles fullscreen; Esc exits.

The player uses GStreamer hardware decoding when available and the i.MX
2D accelerator for a bounded 640 x 360 RGBA preview. GTK preserves the
display aspect ratio. This is not a zero-copy or native-resolution renderer.
Fullscreen state follows the compositor; the button shows the next action.
