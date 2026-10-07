# Video Sources

[Documentation](README.md) · [Project Overview](../README.md)

The suite offers only the two Buildings clips supplied by the user and
identified as Freepik downloads. Each was supplied in 720p and 1080p.

| Clip | Original Filename Pattern | Duration | Frame Rate |
| --- | --- | --- | --- |
| Buildings A | `458687_High_rise_Buildings_<resolution>.mp4` | 34.08 seconds | 25 FPS |
| Buildings B | `458688_High_rise_Buildings_<resolution>.mp4` | 31.80 seconds | 25 FPS |

The menu first selects HD (1280x720) or Full HD (1920x1080), then A or B.
Classification, detection and the player use the same content on each SoM.

| SoM | Installed Video Format | Preparation |
| --- | --- | --- |
| i.MX 8M Plus | H.264 MP4 | Original supplied clips, renamed to `buildings_<id>_<resolution>.mp4` |
| VAR-SOM-MX93 | MJPEG AVI | Converted copies of those clips for CPU decoding |
| DART-MX95 | H.264 MP4 | Compatibility copies without B-frames for the tested decoder path |

Conversion preserves source resolution, frame rate and duration, not the
original encoding. The original files are retained; manifests specify the
SHA-256 checksum of each installed copy. See [camera/video details](../ai-ml-demos/camera-vision/)
for decoding and preprocessing differences.

The original Freepik page URLs and license documents were not supplied.
No independent license verification or new video license is claimed here.
Model license files do not serve as licenses for these videos.

Chicago and Jijiga examples are retired. Updates remove their known,
unchanged suite-installed files by checksum. Changed files, custom videos
and symlink targets are preserved. No external storage objects are deleted.

## Related Guides

- [Input Processing Flow](models.md#image-video-and-camera-input-flow): where the decoder, CPU, G2D/PXP and GPU fit.
- [Video Player](../multimedia-demos/README.md): selection and playback controls.
- [Performance](performance.md): how different decoding paths affect the comparison.
