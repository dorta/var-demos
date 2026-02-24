# Benchmark Summary (Board 192.168.0.10)

Date: 2026-02-24  
Loops: 20  
Warmup: 5  
Delegate: `/usr/lib/libneutron_delegate.so`

## Successful runs

| Model | Mode | Avg ms |
|---|---:|---:|
| palm original | CPU | 104.796 |
| palm original + delegate | NPU attempt (0 delegated) | 104.776 |
| palm neutron converted | NPU | 4.469 |
| landmark original | CPU | 106.113 |
| landmark original + delegate | NPU attempt (0 delegated) | 106.227 |
| landmark neutron converted | NPU (1 delegated) | 102.061 |
| hand_recrop integer_quant original | CPU | 24.839 |
| hand_recrop integer_quant original + delegate | NPU attempt (0 delegated) | 24.865 |
| hand_recrop integer_quant neutron | NPU | 1.593 |
| hand_recrop full_integer_quant original | CPU | 24.672 |
| hand_recrop full_integer_quant original + delegate | NPU attempt (0 delegated) | 24.654 |
| hand_recrop full_integer_quant neutron | NPU | 1.068 |

## Failed to run on this TFLite runtime
- `naruto_handsign_detection_yolox_nano_integer_quant.tflite`
- `naruto_handsign_detection_yolox_nano_full_integer_quant.tflite`
- converted neutron variants of both above

Failure signature:
- `RuntimeError ... activations.cc:470 output->params.scale == 1./256 was not true (LOGISTIC)`

## Conclusion
- Best low-latency candidates on i.MX95 NPU: **palm_neutron** and **hand_recrop_neutron**.
- Landmark model remains the bottleneck for full 21-keypoint gesture pipeline.
