# Accelerated camera and video inference

MobileNet classification and SSD detection for the tested MX93 and MX95
BSPs. Select the demo through `var-demos`; the installer selects compiled
models and labels for the detected board, not another board's artifacts.

The tested camera is OV5640 on `/dev/video0`. MX93 captures 640x480; MX95
captures 1280x720 through CSI0 on the Sonata carrier. Other sensors and
carriers need their own media-controller setup and are not auto-configured.

MX93 uses Vela-compiled models and Ethos-U65. Its SSD post-processing runs
on the CPU. MX95 uses matching Neutron models; SSD-Lite box decoding and
non-maximum suppression run on the CPU. Label indices and SSD anchors are
model-specific. The video resolution is not the model input resolution.

Both High-rise buildings clips are installed in 720p and 1080p at 25 FPS.
Clip A lasts 34.08 seconds; clip B lasts 31.80 seconds. Select a video
before starting classification or detection; 720p is the first choice.
MX93 decodes MJPEG AVI on the CPU. MX95 decodes H.264 MP4 with the hardware
decoder and uses EGL for color conversion. MJPEG copies preserve resolution,
frame rate and duration, but change the encoding and are much larger.

Startup stages report model loading, NPU warmup and the first actual frame.
Esc stops a graphical demo; Ctrl+C stops a direct invocation. Windows and
capture resources are released on exit. Models and media are downloaded
from DigitalOcean Spaces and verified with SHA-256, not Git LFS.

The footer reports the named CPU thermal zone (`cpu-thermal` on MX93 and
`a55-thermal` on MX95), not a separate NPU sensor. Continuous operation
requires cooling. Short validation does not guarantee multi-hour stability.

See the [board comparison](../../README.md) and
[model conversion guide](../../CONVERTING_MODELS.md) for measured results.
