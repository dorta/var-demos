# High-resolution video detection

Object detection on i.MX 8M Plus using GStreamer, SSD MobileNet V1 and the
TensorFlow Lite VX delegate. A resized frame enters the model; detections
are drawn after display scaling. This is a video-pipeline demo, not a new
model or a claim of improved model accuracy.

## Run

Use the [root installer](../../README.md), then run `var-demos`.
Choose **AI / ML → Detect objects in a video with VIP8000**, then the quality
and clip. The separate HD entry has been merged into this common menu.

- HD: 720p, 1280×720.
- Full HD: 1080p, 1920×1080.
- Buildings A: 34 seconds; Buildings B: 32 seconds.

Samples are downloaded from DigitalOcean Spaces and checked with SHA-256.
Only the two user-provided Freepik Buildings clips are offered. Chicago and
Jijiga are retired; their unmodified suite-installed files are removed on update.

Press Esc to stop. The display preserves aspect ratio, with bars when needed.
Text and detection labels use display pixels, not source-video pixels:
720p and 1080p remain equally readable on the same panel. Display presets
select the presentation size without changing the model input.
Decoder, codec and resources limit supported inputs; arbitrary 4K sources
and sustained source-rate inference are not guaranteed. Cooling is required.

## Developer options

From `/opt/var-demos/ai-ml/high-resolution-video-detection`:

```sh
python3 high-resolution-video-detection.py --help
python3 high-resolution-video-detection.py --combination 2 \
  --video /path/to/movie.mp4 --headless
```

Run without arguments to list display presets. `--headless` processes a file
without a window and prints final statistics. Direct GUI execution needs the
display environment normally prepared by `var-demos`.
