# Preparing NPU models

Use separate artifacts for each backend. A `.tflite` suffix alone does not
establish compatibility. Preserve the source model, license, labels,
preprocessing, quantization parameters and compiler version with each asset.

| Board | Model preparation | Runtime delegate |
| --- | --- | --- |
| i.MX 8M Plus | Quantized TFLite; VX prepares its graph | `libvx_delegate.so` |
| i.MX 93 | Quantized TFLite compiled with Vela | `libethosu_delegate.so` |
| i.MX 95 | BSP-compatible Neutron compiled model | `libneutron_delegate.so` |

The backend paths are documented in the
[NXP machine-learning guide](https://www.nxp.com/docs/en/user-guide/UG10166.pdf).
Use the guide and tools matching the installed BSP, not automatically the
newest release.

## Quantization and preprocessing

Quantize with a representative dataset from the intended application.
Check input dtype, scale, zero point, RGB/BGR order, resize policy and output
tensor layout. Do not cast normalized floats directly to unsigned bytes.
For detectors, preserve matching anchors, label indices, box decoding and
non-maximum suppression. These operations may remain on the CPU.

## i.MX 8M Plus

Load a supported quantized TFLite model with the VX delegate. Neither Vela
nor Neutron compilation is used for this backend. Warm up before measuring;
the first invocation includes graph preparation. Check delegation logs for
CPU fallback rather than assuming that loading a delegate accelerates all
operators.

## i.MX 93

Use the Vela version supplied with the BSP. On the tested Scarthgap image,
Vela 3.12.0 successfully compiled MobileNet V1 for Ethos-U65-256:

```sh
vela model_quant.tflite \
  --accelerator-config ethos-u65-256 --output-dir output
```

Load the generated `*_vela.tflite` with the Ethos-U delegate. This command
was tested with MobileNet; it is not a guarantee for arbitrary operators.
The old repository MobileNet artifact failed with this image's TFLite
runtime, while recompiling its uncompiled model with the image's Vela passed.
The NXP examples also
[compile quantized MX93 models with Vela](https://github.com/nxp-imx/nxp-nnstreamer-examples/blob/main/downloads/compile_models.sh).

## i.MX 95

Use the Neutron converter and model artifacts matching the BSP's driver and
firmware. Do not reuse a Vela artifact or copy a converter from an older SDK.
The tested Wrynose 6.18.20 image reported driver microcode 3.1.2; an older
locally compiled SSD reported microcode 3.0.0 and produced a mismatch warning.
That older artifact is not selected for installation.

MobileNet V1 and SSD-Lite camera/video inference were tested using the matching
[NXP model release](https://github.com/nxp-imx-support/nxp-demo-experience-assets/tree/lf-6.18.20_2.0.0/models).
For custom models, follow the matching SDK converter instructions. A custom
conversion with the current SDK has not yet been validated in this project.
Use the BSP's `tflite_runtime` with its delegate. On this image, switching
to the installed `ai_edge_litert` runtime crashed during tensor allocation;
the presence of an importable runtime does not establish delegate ABI
compatibility.

## Validation before publishing

1. Confirm the intended NPU subgraph is delegated; XNNPACK is CPU execution.
2. Compare predictions with the source model on fixed reference inputs.
3. Measure warm inference separately from full camera/video throughput.
4. Check cleanup, restart, memory growth and named thermal sensors over time.
5. Publish the artifact externally with its SHA-256 and license, then update
   the platform catalog only after testing the installed demo.

NPU availability does not imply video decoder availability. The tested MX93
image has a working camera but no GStreamer H.264 decoder. Its video demos
use MJPEG AVI copies decoded on the CPU, preserving source resolution,
frame rate and duration. This does not preserve the original encoding or
make video throughput a like-for-like comparison with the other boards.
