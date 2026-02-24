# FaceDet NPU Demo (from eIQ model zoo)

Model source:
- `eiq-model-zoo/tasks/vision/object-detection/faceDet/yolo_face_detect.tflite`

Converted model:
- `yolo_face_detect_neutron.tflite`

## Run
```bash
python3 main.py
```

Optional:
```bash
python3 main.py --camera /dev/video13 --use-npu 1
python3 main.py --camera /dev/video0 --use-npu 0 --windowed
```

## Behavior
- Detects faces on camera stream
- Draws boxes + confidence score
- Shows inference time and FPS

## Notes
- `--use-npu 1` selects `yolo_face_detect_neutron.tflite`
- `--use-npu 0` selects original TFLite model
