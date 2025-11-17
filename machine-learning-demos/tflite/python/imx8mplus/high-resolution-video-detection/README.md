# High-resolution Object Detection Demo (DART-MX8M-PLUS/VAR-SOM-MX8M-PLUS)

This demo showcases real-time object detection on the
DART-MX8M-PLUS/VAR-SOM-MX8M-PLUS SoMS, combining hardware-accelerated GStreamer
video decoding with TensorFlow Lite running on the integrated NPU (Vivante VX
Delegate).

The application:

* Plays real video files at their native resolution;
* Extracts frames with GStreamer and `appsink`;
* Runs object detection with TFLite + NPU delegate;
* Draws bounding boxes and labels using OpenCV;
* Displays the output on LVDS or HDMI in either windowed or fullscreen mode.

The code is optimized to handle **high-resolution sources** (720p, 800p, 1080p
and beyond) smoothly and consistently, while remaining **resolution-agnostic**.

## 1. Video Files

**No video files are included in this repository** due to copyright restrictions.

The paths listed inside the `COMBINATIONS` table (e.g.
`video_1280x720.mp4`) are **only placeholders**.

To run this demo, you must:

* Provide your own video files;
* Put them in the expected folder directories **or**;
* Modify the `COMBINATIONS` entries to point to your custom paths.

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
    "video_1280x720.mp4",
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

There is no need to follow combinations, you can:

* Replace placeholder files with your own;
* Modify any entry inside `COMBINATIONS`;

The only requirement is that the width/height information is correct so that
fullscreen rendering and AR calculation behave properly.

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

## 4. Running the Demo

List the available combinations:

```sh
python3 high-resolution-video-detection.py
```

Run the demo:

```sh
python3 high-resolution-video-detection.py --combination 3
```

## 5. Using Your Own Videos

Because the script does **not** expose `--video`, use one of the two methods:

### Option A: Replace the placeholder videos

Just keep the filenames and overwrite the content.

### Option B: Edit `COMBINATIONS`

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
* Preserves aspect ratio;
* Adds black bars when necessary.

## 7. License

```sh
Copyright 2025 Variscite Ltd.
SPDX-License-Identifier: BSD-3-Clause
```