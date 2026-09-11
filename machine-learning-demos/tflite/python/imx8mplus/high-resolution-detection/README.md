<!-- Copyright 2026 Variscite Ltd. -->
<!-- SPDX-License-Identifier: BSD-3-Clause -->

# HD and Full HD object detection

This application decodes an H.264 MP4 with GStreamer, converts frames with the
i.MX G2D element, runs SSD MobileNet inference, and draws the result with
OpenCV.

From the repository root, use the short launcher:

```bash
./ml-demo hd --combination 1 \
  --source /path/to/1280x720-video.mp4 \
  --headless --max-frames 1 \
  --output-frame /tmp/hd-result.png
```

Combination 1 describes an HD 1280x720 input. Combination 13 describes a Full
HD 1920x1080 input. Run `./ml-demo hd` to list every display combination.

Options added for repeatable validation:

- `--source`: override the video associated with the selected combination.
- `--headless`: do not create an OpenCV display window.
- `--max-frames`: stop after a bounded number of frames; zero means all.
- `--output-frame`: save the latest annotated frame as an image.

The repository does not need to carry large test videos. Supply licensed media
through `--source`; this also avoids failures when a Git LFS checkout contains
pointer text instead of actual MP4 data.

Delegate loading does not guarantee that every model operator runs on the NPU.
Inspect runtime warnings for CPU fallback and benchmark the complete graph.
