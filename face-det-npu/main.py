#!/usr/bin/env python3

import argparse
import ctypes
import time
from pathlib import Path

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite


ANCHORS = [
    np.array([[51, 64], [59, 82], [79, 100]], dtype=np.float32),
    np.array([[29, 51], [36, 43], [41, 54]], dtype=np.float32),
    np.array([[15, 21], [22, 29], [28, 36]], dtype=np.float32),
]


def find_delegate(explicit=""):
    cands = [explicit, "/usr/lib/libneutron_delegate.so", "/usr/lib/liblitert_neutron_delegate.so"]
    for c in cands:
        if not c:
            continue
        if not Path(c).is_file():
            continue
        try:
            ctypes.CDLL(c)
            return c
        except OSError:
            pass
    return ""


def list_cameras():
    return [str(d) for d in sorted(Path("/dev").glob("video*"))]


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def non_max_suppress(boxes, scores, iou_thresh=0.5, max_boxes=20):
    if len(boxes) == 0:
        return []
    idxs = np.argsort(scores)[::-1]
    picked = []
    while len(idxs) > 0 and len(picked) < max_boxes:
        i = idxs[0]
        picked.append(i)
        if len(idxs) == 1:
            break
        rest = idxs[1:]

        xx1 = np.maximum(boxes[i, 0], boxes[rest, 0])
        yy1 = np.maximum(boxes[i, 1], boxes[rest, 1])
        xx2 = np.minimum(boxes[i, 2], boxes[rest, 2])
        yy2 = np.minimum(boxes[i, 3], boxes[rest, 3])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h

        area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        area_r = (boxes[rest, 2] - boxes[rest, 0]) * (boxes[rest, 3] - boxes[rest, 1])
        union = area_i + area_r - inter + 1e-6
        iou = inter / union
        idxs = rest[iou < iou_thresh]
    return picked


def image_resize_letterbox(img, dst_w, dst_h):
    h, w = img.shape[:2]
    scale = min(dst_w / w, dst_h / h)
    nw, nh = int(w * scale), int(h * scale)
    dx, dy = (dst_w - nw) // 2, (dst_h - nh) // 2
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    out = np.ones((dst_h, dst_w, 3), np.uint8) * 128
    out[dy : dy + nh, dx : dx + nw] = resized
    return out


def decode(out, anchor, in_shape, img_shape, conf=0.35, nms_iou=0.45):
    gh, gw, ch = out.shape
    out = out.reshape((gh, gw, 3, ch // 3))

    out[..., :2] = _sigmoid(out[..., :2])
    out[..., 4:] = _sigmoid(out[..., 4:])
    out[..., 5:] *= out[..., 4][..., np.newaxis]

    net_h, net_w = in_shape[1], in_shape[2]
    img_h, img_w = img_shape[:2]

    if (float(net_w) / img_w) < (float(net_h) / img_h):
        new_w = net_w
        new_h = (img_h * net_w) / img_w
    else:
        new_h = net_h
        new_w = (img_w * net_h) / img_h

    x_offset, x_scale = (net_w - new_w) / 2.0 / net_w, float(net_w) / new_w
    y_offset, y_scale = (net_h - new_h) / 2.0 / net_h, float(net_h) / new_h

    col = np.arange(gw).reshape(1, gw, 1, 1)
    row = np.arange(gh).reshape(gh, 1, 1, 1)

    x = (col + out[..., 0:1]) / gw
    y = (row + out[..., 1:2]) / gh
    aw = anchor[:, 0].reshape(1, 1, 3, 1)
    ah = anchor[:, 1].reshape(1, 1, 3, 1)
    w = aw * np.exp(out[..., 2:3]) / net_w
    h = ah * np.exp(out[..., 3:4]) / net_h

    x = (x - x_offset) * x_scale
    y = (y - y_offset) * y_scale
    w *= x_scale
    h *= y_scale

    x1 = (x - w / 2) * img_w
    y1 = (y - h / 2) * img_h
    x2 = (x + w / 2) * img_w
    y2 = (y + h / 2) * img_h

    score = out[..., 4].reshape(-1)
    coords = np.stack([x1.reshape(-1), y1.reshape(-1), x2.reshape(-1), y2.reshape(-1)], axis=1)

    m = score > conf
    if not np.any(m):
        return []

    coords = coords[m]
    score = score[m]
    keep = non_max_suppress(coords, score, iou_thresh=nms_iou, max_boxes=30)
    return [(coords[i], float(score[i])) for i in keep]


class FaceDetector:
    def __init__(self, model_path, delegate_path=""):
        delegates = [tflite.load_delegate(delegate_path)] if delegate_path else None
        self.interp = tflite.Interpreter(model_path=str(model_path), experimental_delegates=delegates)
        self.interp.allocate_tensors()
        self.in_det = self.interp.get_input_details()[0]
        self.out_det = self.interp.get_output_details()
        self.in_shape = self.in_det["shape"]

    def infer(self, bgr):
        _, h, w, _ = self.in_shape
        inp = image_resize_letterbox(bgr, int(w), int(h))
        inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB)

        zp = self.in_det["quantization_parameters"].get("zero_points", [0])[0]
        sc = self.in_det["quantization_parameters"].get("scales", [1.0])[0]
        x = (inp / 255.0 / sc + zp).astype(self.in_det["dtype"])

        self.interp.set_tensor(self.in_det["index"], x.reshape(self.in_shape))
        self.interp.invoke()

        boxes = []
        for i, od in enumerate(self.out_det):
            out = self.interp.get_tensor(od["index"])[0]
            ozp = od["quantization_parameters"].get("zero_points", [0])[0]
            osc = od["quantization_parameters"].get("scales", [1.0])[0]
            out = ((out.astype(np.float32) - ozp) * osc).astype(np.float32)
            boxes.extend(decode(out, ANCHORS[i], self.in_shape, bgr.shape))
        return boxes


def parse_args():
    ap = argparse.ArgumentParser(description="FaceDet NPU demo (i.MX95)")
    ap.add_argument("--camera", default="")
    ap.add_argument("--use-npu", choices=["0", "1"], default="1")
    ap.add_argument("--windowed", action="store_true")
    return ap.parse_args()


def main():
    args = parse_args()
    base = Path(__file__).resolve().parent

    cams = list_cameras()
    if not cams:
        print("No /dev/video* found")
        return 1

    camera = args.camera
    if not camera:
        print("Available cameras:")
        for i, c in enumerate(cams):
            print(f"  [{i}] {c}")
        pick = input("Camera index [0]: ").strip()
        camera = cams[int(pick)] if pick.isdigit() and int(pick) < len(cams) else cams[0]

    delegate = find_delegate() if args.use_npu == "1" else ""
    use_npu = bool(delegate)
    model = base / "assets" / ("yolo_face_detect_neutron.tflite" if use_npu else "yolo_face_detect.tflite")

    det = FaceDetector(model, delegate)

    cap = cv2.VideoCapture(camera, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    ok, frame = cap.read()
    if not ok:
        print(f"Cannot read from {camera}")
        return 2

    print(f"Input: {camera}")
    print(f"Delegate: {delegate if use_npu else 'CPU'}")
    print(f"Model: {model.name}")

    win = "FaceDet NPU"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    if not args.windowed:
        cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    fps = 0.0
    last = time.time()
    while ok:
        t0 = time.perf_counter()
        boxes = det.infer(frame)
        inf_ms = (time.perf_counter() - t0) * 1000.0

        for b, s in boxes:
            x1, y1, x2, y2 = [int(v) for v in b]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{s:.2f}", (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        now = time.time()
        dt = max(now - last, 1e-6)
        fps = (0.9 * fps + 0.1 * (1.0 / dt)) if fps else (1.0 / dt)
        last = now

        cv2.putText(frame, f"Infer: {inf_ms:.2f} ms", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Faces: {len(boxes)}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (40, 255, 40), 2)

        cv2.imshow(win, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        ok, frame = cap.read()

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
