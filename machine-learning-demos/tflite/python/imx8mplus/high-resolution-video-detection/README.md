# High-resolution Object Detection Demo for i.MX 8M Plus

This demo showcases real-time object detection on i.MX 8M Plus platforms,
including the DART-MX8M-PLUS and VAR-SOM-MX8M-PLUS. It combines
hardware-accelerated GStreamer video processing with TensorFlow Lite running
through the Vivante VX delegate.

The application:

* Plays real video files at their native resolution;
* Extracts frames with GStreamer and `appsink`;
* Runs object detection with TFLite + NPU delegate;
* Draws bounding boxes and labels using OpenCV;
* Displays the output on LVDS or HDMI in either windowed or fullscreen mode.

The code is optimized to handle **high-resolution sources** (720p, 800p, 1080p
and beyond) smoothly and consistently, while remaining **resolution-agnostic**.

## 1. Video Files

**No video files are included directly in this repository.** Validation samples
are hosted separately and installed with `install.sh`, keeping large binaries
out of Git.

The paths listed inside the `COMBINATIONS` table point to files under
`assets/videos/`.

To prepare the included samples and check the target runtime:

```sh
./install.sh
```

The installer downloads assets with `curl`, retries transient failures, and
validates every file against the published `SHA256SUMS` manifest. By default it
uses the versioned URL:

```text
https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/high-resolution-video-detection/v1/samples
```

`ASSET_VERSION`, `ASSET_BASE_URL`, and `ASSET_DIR` can be overridden in the
environment. For example:

```sh
ASSET_VERSION=v2 ./install.sh
```

You can also:

* provide your own video with `--video`; or
* modify the `COMBINATIONS` entries to point to custom paths.

The `COMBINATIONS` table defines presets used to simplify usage on the EVK.

Each entry includes:

* Video file path;
* Video resolution;
* Target display (LVDS small, LVDS large, 4K HDMI);
* Display resolution;
* Display mode (windowed / fullscreen).

### Example

```sh
(
    "assets/videos/video_1280x720.mp4",
    (1280, 720),
    "lvds_small",
    (800, 480),
    "windowed"
)
```

Meaning:

* Play a 1280×720 video;
* Resize frames for the model internally;
* Show on the 800×480 LVDS display;
* Use a windowed OpenCV window.

You do not have to use the preset video paths. You can:

* Pass a file directly with `--video`;
* Replace a placeholder file with your own; or
* Modify an entry inside `COMBINATIONS`.

The video-size fields describe each preset in the printed list. GStreamer reads
the actual source size from the decoded stream. The display-size field controls
the fullscreen output and its aspect-ratio-preserving letterbox.

## 2. Supported Video Resolutions

The pipeline supports **any video resolution**. This works because the decoded
frame is always resized internally to the model's input size before inference,
making the system **resolution‑agnostic**.

Supported examples:

* **Low/medium resolutions:** 480p, 640×480, 800×480, etc;
* **Standard high resolutions:** 720p, 800p, 1080p, etc;
* **EVK-specific resolutions:** 1280×800, 800×480, etc;
* **Non-standard:** 1024×600, 1366×768, 1600×900, etc;
* **High resolutions:** 1440p, 2K, 4K (depending on SoM performance), etc;
* **All aspect ratios:** 16:9, 16:10, 5:3, 4:3, ultrawide, etc.

Inference occurs on the resized frame:

```sh
resized = cv2.resize(frame, (model_width, model_height))
```

The only parts dependent on correct resolution metadata are:

* Fullscreen placement;
* Aspect ratio handling;
* Display scaling.

## 3. What This Demo Adds

This demo does not change the object-detection model or claim a new NPU
optimization over the NXP inference examples. Its improvements are in the
end-to-end video and display pipeline:

* GStreamer decodes the source and uses the i.MX G2D converter before frames
  reach the application;
* `appsink` passes decoded frames directly to the Python processing loop and
  drops stale frames when inference cannot keep up with the source frame rate;
* only a model-sized copy of each frame is submitted to TensorFlow Lite, while
  detections are drawn on the original-resolution frame;
* the VX delegate runs compatible TensorFlow Lite operations on the i.MX 8M
  Plus NPU, while unsupported operations can fall back to the CPU; and
* the application provides LVDS/HDMI windowed and fullscreen presentation,
  including aspect-ratio-preserving letterboxing.

The main benefit compared with a basic image or console inference example is
therefore the complete real-time path from compressed video through NPU
inference to an annotated display.

## 4. Running the Demo

List the available combinations:

```sh
python3 high-resolution-video-detection.py
```

Run the demo:

```sh
python3 high-resolution-video-detection.py --combination 3
```

Run a preset with a custom video:

```sh
python3 high-resolution-video-detection.py \
    --combination 3 \
    --video /path/to/video.mp4
```

For automated validation without a display window, add `--headless`.
The application prints the number of processed frames and detections when the
video ends, which makes headless smoke tests easy to verify.

On an NXP i.MX XWayland image with Weston, an SSH session can launch the GUI
through XWayland as follows:

```sh
export XDG_RUNTIME_DIR=/run/user/0
export DISPLAY=:0
python3 high-resolution-video-detection.py \
    --combination 2 \
    --video /path/to/video.mp4
```

The demo was validated on an i.MX 8M Plus system running the Variscite
6.6.144 `var-lts-next` kernel with an 800x480 LVDS display. The validation used
V4L2 hardware H.264 decoding, the i.MX G2D converter, and the VX delegate.

## 5. Using Your Own Videos

Use one of the following methods:

### Option A: Select a video on the command line

```sh
python3 high-resolution-video-detection.py \
    --combination 3 \
    --video /path/to/video.mp4
```

### Option B: Replace a placeholder video

Just keep the filenames and overwrite the content.

### Option C: Edit `COMBINATIONS`

Example:

```sh
(
    "my-videos/drone_1440x900.mp4",
    (1440, 900),
    "monitor_4k",
    (3840, 2160),
    "fullscreen"
)
```

After adding this entry, run with:

```
--combination <ID>
```

## 6. Display Modes

### Windowed Mode

* Adjustable OpenCV window;
* Keeps aspect ratio;
* No distortion.

### Fullscreen Mode

* Covers the entire display;
* Preserves aspect ratio; and
* Adds black bars when necessary.

## 7. Reference Result Videos

Two historical 1280x720 result videos were recovered from the Variscite
DigitalOcean Space and preserved under:

```text
https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/high-resolution-video-detection/v1/reference/
```

They already contain rendered labels and bounding boxes, so they are reference
outputs rather than clean demo inputs. Their `SHA256SUMS` file is published in
the same directory.

## 8. License

```sh
Copyright 2025 Variscite Ltd.
SPDX-License-Identifier: BSD-3-Clause
```
