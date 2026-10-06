# Multimedia demos

Use the [root installer](../README.md), then launch the video player from
the **Multimedia** category in `var-demos`.

Open a local movie. Use Play/Pause, Stop, the seek bar and volume slider.
Space toggles playback; S stops; F toggles fullscreen; Esc exits.

The player uses GStreamer hardware decoding when available and the i.MX
G2D (MPlus), PXP (MX93) or EGL (MX95) for a bounded RGBA preview.
GTK preserves the
display aspect ratio. This is not a zero-copy or native-resolution renderer.
Fullscreen state follows the compositor; the button shows the next action.
The header uses the Variscite logo, downloaded and SHA-256 verified by the
installer. High-rise buildings A in 720p is installed as the default.
Open selects a local movie. The AI/ML video selector also includes both
High-rise clips in 720p and 1080p, downloaded by the same installer.
MX93 uses MJPEG AVI copies because the tested image lacks an H.264 decoder.
