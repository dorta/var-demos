# Accelerated camera and video inference

MobileNet classification and SSD detection for the tested MX93 and MX95
BSPs. Select the demo through `var-demos`; the installer selects compiled
models and labels for the detected board, not another board's artifacts.

The tested camera is OV5640 on `/dev/video0`. MX93 defaults to 640x480;
MX95 defaults to 1280x720 through CSI0 on the Sonata carrier. The menu
also offers VGA, 720p and 1080p capture; this configures the sensor and
capture pipeline, not just an upscaled display. Other sensors and
carriers need their own media-controller setup and are not auto-configured.

MX93 uses Vela-compiled models and Ethos-U65. Its SSD post-processing runs
on the CPU. MX95 uses matching Neutron models; SSD-Lite box decoding and
non-maximum suppression run on the CPU. Label indices and SSD anchors are
model-specific. The video resolution is not the model input resolution.

The shared menu starts with classification (image, video, camera), followed
by detection (image, video, camera). Sample image predictions stay visible
until Esc. All views use the shared MPlus-style panels and fullscreen.

Both High-rise buildings clips are installed in 720p and 1080p at 25 FPS.
Clip A lasts 34.08 seconds; clip B lasts 31.80 seconds. Select a video
before starting classification or detection; 720p is the first choice.
MX93 decodes MJPEG AVI on the CPU. MX95 decodes H.264 MP4 with the hardware
decoder and uses EGL for color conversion. MJPEG copies preserve resolution,
frame rate and duration, but change the encoding and are much larger.

File video is decoded at its selected resolution, then resized to fit the
display by the BSP converter: PXP on MX93 and G2D on MPlus.
On an 800x480 display, a 16:9 source becomes an 800x450 working image,
then is resized to the model's 224x224 or 300x300 input. This reduces CPU
copies and scaling, but introduces an additional resampling step; prediction
equivalence to native-frame preprocessing has not been established.
Set `VAR_AI_NATIVE_FRAMES=1` before a direct invocation to compare the
original native-frame path. MX95 retains native-frame EGL conversion by
default; scaled EGL is experimental, enabled only with
`VAR_AI_ACCELERATED_VIDEO=1`, pending a cooled-board retest.
Video playback follows the file clock; there is
no extra cold-board frame limiter. Thermal limits still apply: 15 FPS
above 80 C, pause at 82 C, resume below 78 C. The decoder is paused too
during cooling on MX93/MX95 and in the MPlus HD-specific runner, and is not
started on a hot MX93/MX95 before cooling. The shared MPlus OpenCV capture
backend cannot pause its decoder, so that path retains inference-only cooling.
The summary's peak temperature is the hottest sampled SoC/CPU zone; the
on-screen footer still shows its named board sensor.

MX95 samples use the `media/ordered-v2/` asset release: H.264 re-encoded
without B-frames as compatibility copies. Crucially, the decoder uses
explicit MMAP NV12 buffers before GPU upload: removing B-frames alone did
not eliminate stale/future images in the automatic DMA_DRM/EGL path.
The final pipeline was compared with an independent CPU decode of the same
file: 245 consecutive frames matched reference order with no regressions.
Source resolution, frame rate and duration are retained; encoding
is not bit-identical. The original files are not overwritten. Preparation:

```sh
ffmpeg -i input.mp4 -an -c:v libx264 -preset fast -crf 18 -bf 0 -g 50 -pix_fmt yuv420p -movflags +faststart output.mp4
```

Annotations are drawn after fitting the image to the display, so 720p and
1080p use the same readable text size on an 800x480 panel. Letterboxing
preserves aspect ratio and detection coordinates; model input is unchanged.
The framebuffer supplies the display size; `VAR_AI_DISPLAY_SIZE=800x480`
overrides it when needed.

Startup stages report model loading, NPU warmup and the first actual frame.
Esc stops a graphical demo; Ctrl+C stops a direct invocation. Windows and
capture resources are released on exit. Models and media are downloaded
from DigitalOcean Spaces and verified with SHA-256, not Git LFS.

The footer reports the named CPU thermal zone (`cpu-thermal` on MX93 and
`a55-thermal` on MX95), not a separate NPU sensor. Continuous operation
requires cooling. Short validation does not guarantee multi-hour stability.

See the [board comparison](../../README.md) and
[model conversion guide](../../CONVERTING_MODELS.md) for measured results.
