# Multimedia demos

Launch the video player from `var-demos`, or run `var-media` directly.

Open a local movie. Use Play/Pause, Stop, the seek bar and volume slider.
Space toggles playback; S stops; F toggles fullscreen; Esc exits.

This first GTK/GStreamer player uses a bounded 640 x 336 preview, preserving
aspect ratio. Decoder choice depends on the installed GStreamer plugins;
this is not yet a zero-copy or native-resolution renderer.
