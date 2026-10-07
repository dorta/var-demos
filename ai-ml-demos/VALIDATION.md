# Cross-board presentation and playback validation

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
are in [the conversion guide](../CONVERTING_MODELS.md).

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
