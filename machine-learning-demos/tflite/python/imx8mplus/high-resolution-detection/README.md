# High-Resolution ML Demo on the DART-MX8M-PLUS

This example presents how to run a high-resolution, real-time object detection
demo on the DART-MX8M-PLUS System on Module (SoM), using HD (1280×720p) and
Full HD (1920×1080p) video files accelerated by the integrated NPU through
the TensorFlow Lite delegate resource.

The resulting example plays actual video files, renders live detections with
OpenCV, and displays output on either LVDS or HDMI screens in both windowed
and full-screen modes.

While the official NXP i.MX Machine Learning User's Guide provides useful
references samples, those are often limited to console-only applications
or static image inferences, lacking video playback, user interaction,
support for common display resolutions, and real-world resolution support.

Variscite developed this example to fill those gaps and push the platform
closer to production-grade use. This demo introduces real-time object
detection accelerated by the NPU, with on-screen rendering via OpenCV,
supporting both LVDS and HDMI outputs at HD and Full HD resolutions.
Unlike basic SDK or BSP samples, this can serve as a foundation for
real-world applications with further development.

**Note:**
This project uses [Git Large File Storage (LFS)](https://git-lfs.github.com/)
to manage large video files in the `media/` directory.

To ensure the video files are properly downloaded:

1. Install Git LFS:
    ```bash
    sudo apt install git-lfs
    ```

2. Perform the one-time Git LFS setup:
    ```bash
    git lfs install
    ```

3. Clone this repository as usual:
    ```bash
    git clone git@github.com:varigit/var-demos.git
    ```

4. In most cases, Git LFS will automatically download the large files during
   the clone. If the video files appear as small text placeholders, run:
    ```bash
    git lfs pull
    ```

If Git LFS is not installed, video files will appear as small text placeholders
and will not play correctly.
