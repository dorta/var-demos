# High-resolution video detection

Object detection on i.MX 8M Plus using GStreamer, SSD MobileNet V1 and the
TensorFlow Lite VX delegate. A resized frame enters the model; detections
are drawn before display scaling. This is a video-pipeline demo, not a new
model or a claim of improved model accuracy.

## Run

Use the [root installer](../../README.md), then run `var-demos`.
Choose **AI / ML → Detect objects in a high-resolution video**, then a sample:

- Chicago traffic: 1280×720.
- Jijiga street: 1280×720, 1280×800 or 1920×1080.

Samples are downloaded from DigitalOcean Spaces and checked with SHA-256.
The original `combined_videos` LFS objects have not been recovered; these
are replacement samples, not the original compilations.
Jijiga variants come from [Brian Dell's CC0 footage](https://commons.wikimedia.org/wiki/File:Jijiga.ogv).

Press Esc to stop. The display preserves aspect ratio, with bars when needed.
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
