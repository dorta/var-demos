# Cross-board presentation and playback validation

[Documentation](README.md) · [Project Overview](../README.md)

This record includes historical checks of the earlier eight-video catalog.
The current catalog offers only Buildings A and B in HD and Full HD.

Requested checks for i.MX 8M Plus, VAR-SOM-MX93 and DART-MX95:

- Use the same wording for shared demos, followed by the actual NPU name.
- Show the same eight video samples in the same order on every board.
- Keep board-specific codecs and models; never imply identical capabilities.
- Use the MPlus colors, typography, panels and labels for every vision demo.
- Anchor inference, FPS, model and temperature panels to fixed screen positions.
- Keep classification scores in fixed columns and boxes attached to objects.
- Preserve readability on the 800x480 displays for HD and Full HD sources.
- Investigate reported backward/forward motion in MX95 video inference.
- Validate frame ordering and ownership, not only frame count or inference time.
- Keep thermal protections enabled and distinguish smoothness from correctness.

## Completed checks

The same six primary menu entries appear first on every board: classification
(image, video, camera), then detection (image, video, camera). The actual
NPU is named VIP8000, Ethos-U65 or Neutron. Optional extras follow.

| Check | i.MX 8M Plus | VAR-SOM-MX93 | DART-MX95 |
| --- | --- | --- | --- |
| Image classification / detection displayed | Passed | Passed | Passed |
| 720p / 1080p classification and detection displayed | Passed | Passed | Passed |
| VGA / HD / Full HD camera classification and detection | Passed | Passed | Passed |
| Fixed 800×480 panels and readable labels | Passed | Passed | Passed |
| Identical eight-video menus and manifest coverage | Passed | Passed | Passed |
| Additional SD 720×480 camera mode | Passed | Not offered | Not offered |
| Hand sample with shared overlay | Passed, experimental | Not offered | Not offered |

Graphical checks captured annotated frames, verified display dimensions and
non-black reference imagery, and exercised shutdown with Esc. They are short
functional checks, not sustained FPS benchmarks: saving screenshots on each
frame adds overhead. Do not substitute these rates into performance tables.
MPlus warmup now happens before measured inference, matching the other boards.
An explicit BGR camera caps filter fixes grayscale negotiation at larger
capture resolutions. The root suite forwards video-source and camera-mode
metadata to the shared launcher; direct CLI listing was checked on all boards.

## MX95 forward/backward playback

The problem was reproduced: the automatic hardware decoder / DMA_DRM / EGL
path supplied increasing PTS but visually reordered images. Matching 245
captured frames to an independent CPU-decoded reference exposed 93 backward
transitions in one run. Removing B-frames alone reduced the problem but still
left stale images around GOP boundaries; this alone was not accepted as a fix.

The final pipeline uses `qtdemux ! h264parse ! v4l2h264dec capture-io-mode=2 !
video/x-raw,format=NV12` before GPU upload. In the same 720p comparison,
245 captured frames matched reference frames 0–244 in order, with **zero
backward transitions**. The installed samples use SHA-256-verified
`media/ordered-v2/` compatibility copies; originals are retained externally.
HD and Full HD classification/detection were retested with the final path.

The GTK player's hardware decoder also selects MMAP on MX95. Its integration
check passed play, pause, seeking, stop, restart, fullscreen toggling and close,
with decoded non-black, opaque frames. This does not certify all arbitrary
user files, long-term stability or absence of thermal pauses.

## Model reproduction

Vela 3.12.0 recompilation of both MPlus source models on MX93 reproduced the
installed artifacts byte-for-byte. MobileNet input/output are UINT8;
SSD input is UINT8 with FLOAT32 detection outputs. MX95 uses separate
NXP UINT8-input/FLOAT32-output compiled artifacts; no current-SDK custom
Neutron conversion or equal-weight claim is made. Details and SHA-256 values
are in [the conversion guide](model-conversion.md).

## Installer and removal

The full candidate installer was run on all three boards in disposable
prefixes, preserving their active `/opt/var-demos` installations. All installed
AI assets were SHA-256 checked: 22 manifest entries on MPlus, 15 on MX93 and
16 on MX95 (shared assets can occur in more than one demo manifest).
Installed menu listing and the shared overlay module were checked too.

Removal passed on every board with no asset, executable or symlink left
in the disposable prefixes. Installation metadata now records a custom
command directory so `var-demos --uninstall` removes that launcher too;
older empty markers retain the `/usr/bin` default. Only the temporary
test installations were removed; the active board installations were kept.

Local regression suites: 77 AI tests and 44 suite/installer/documentation
tests passed. Functional board checks above are additional to those suites.

## Video Processing Optimization, 2026-10-07

The user-provided Buildings A source is 25 FPS, not 30 FPS. Native-frame
profiling found CPU resize and display/event work outside the roughly 9 ms
SSD inference. Changing OpenCV to one thread did not improve throughput.
Nearest-neighbor preview was investigated but not selected; BSP accelerated
conversion was used instead, preserving the preview's aspect ratio.

The file is still decoded at 720p or 1080p. G2D (MPlus) and PXP (MX93)
convert it to an 800x450 working image before CPU model resizing and overlay
drawing. Model dimensions, weights and data types are unchanged, but this
adds a resampling step: prediction equivalence has not been established.
`VAR_AI_NATIVE_FRAMES=1` preserves the older native-frame preprocessing.

All recorded runs below displayed 200 annotated frames in fullscreen at
800x480, with a non-black first-frame check. One first-frame screenshot was
saved per run. Rates use the demo's processing interval, excluding model
warmup. Runs used temporary source trees and the installed verified assets.

| SoM | Task | Source | Processing FPS | Mean Inference |
| --- | --- | --- | ---: | ---: |
| MPlus | Classification | 720p H.264 | 24.11 | 3.42 ms |
| MPlus | Classification | 1080p H.264 | 23.99 | 3.70 ms |
| MPlus | Detection | 720p H.264 | 23.74 | 9.00 ms |
| MPlus | Detection | 1080p H.264 | 23.75 | 9.21 ms |
| MX93 | Classification | 720p MJPEG | 24.11 | 4.15 ms |
| MX93 | Classification | 1080p MJPEG | 24.12 | 4.14 ms |
| MX93 | Detection | 720p MJPEG | 24.19 | 9.33 ms |
| MX93 | Detection | 1080p MJPEG | 23.97 | 9.14 ms |

Repeated warmed MPlus detection runs gave 15.06 and 16.82 FPS, while cooler
retests reached 23.74/23.75 FPS. Its thermal pacing uses the hottest SoC/CPU
zone, which can be hotter than the footer sensor. This is not a guarantee of
24 FPS under prolonged load. The HD-specific extra runner separately gave
20.23 FPS at 720p and is not the common-menu detection measurement above.

Clocked files no longer have an additional cold-board rate limiter. Hot-board
15 FPS limiting, 82 C pause and below-78 C resume remain. MX93/MX95 GI capture
pauses the decoder during cooling; the MPlus HD-specific runner does too.
The common MPlus OpenCV backend still has inference-only cooling.
Padded buffer stride, offset and bottom rows are now handled explicitly.

MX95 remained around 81-86 C even without an inference demo, so the new
scaled EGL path could not be safely performance-validated. It remains
experimental (`VAR_AI_ACCELERATED_VIDEO=1`); the default retains the earlier
validated native-frame/MMAP EGL path. A five-second hot-board startup check
confirmed cooling occurs before model/decoder initialization, with zero
inferences and no decoder started. Retesting performance and frame order
with adequate cooling is still required; no new MX95 FPS is claimed.

Local regression: 84 AI tests and 48 suite tests passed before publication.

## Documentation and Detection Overlay Update, 2026-10-07

The guides were reorganized under `docs/`, retaining historical measurement
records. Relative links and heading anchors were checked. Per-NPU guides now
separate model requirements, libraries, startup, classification, detection
and software/hardware responsibilities.

Detection's FPS and inference values use a shared pixel-aligned numeric column.
A fixed panel below FPS displays original stream dimensions, not the scaled
working image, display size or model tensor size. Stream metadata was checked
for Buildings A at 1280x720 and 1920x1080 on all three connected SoMs using
temporary review modules. The panel rendered in memory on each target, and a
clean decoded MX93 frame was inspected for readability. Preview timing values
were illustrative layout values, not new performance measurements.

Regression: 98 AI tests and 51 suite tests passed. This update does not establish
new sustained FPS, prediction equivalence or cooled MX95 inference performance.

## Related Guides

- [Performance](performance.md): the current per-SoM measurement tables.
- [Models and Processing Flows](models.md): model identities and CPU/NPU responsibilities.
- [Video Sources](video-sources.md): the current curated clip catalog and format preparation.
