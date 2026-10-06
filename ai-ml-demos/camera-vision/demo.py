#!/usr/bin/env python3
# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic

import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter, load_delegate

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import (demo_session, managed_capture, record_inference,
                     register_cleanup, startup_step, ThermalPacer,
                     display_view, display_box)
from telemetry import SoCTemperature
from postprocess import decode_postprocessed, decode_ssdlite

ROOT = Path(__file__).resolve().parent
COLORS = [(52, 211, 153), (245, 189, 66), (223, 147, 70), (194, 133, 246)]


def capture_tail(video):
    # OpenCV discovers manual-pipeline sinks by name, unlike our GI reader.
    name = 'frames' if video else 'opencvsink'
    return ('videoconvert ! video/x-raw,format=BGR ! '
            f'appsink name={name} max-buffers=1 drop=true')


def gpu_video_conversion():
    # Force a GL render before download. The BSP's direct conversion path
    # negotiates RGBA but can return entirely zeroed CPU pixels. No size caps:
    # preserve native video dimensions for inference.
    return ('glupload ! glcolorconvert ! glcolorscale ! '
            'video/x-raw(memory:GLMemory),format=RGBA ! gldownload ! '
            'video/x-raw,format=RGBA ! ')


def board():
    compatible = Path('/proc/device-tree/compatible').read_bytes().split(b'\0')
    for name in ('imx93', 'imx95'):
        if ('fsl,' + name).encode() in compatible:
            return name
    raise RuntimeError('This demo requires a tested i.MX 93 or i.MX 95')


def configure_camera(platform, device):
    if device != '/dev/video0':
        raise RuntimeError('Only the tested OV5640 /dev/video0 is supported')
    if platform == 'imx93':
        topology = subprocess.check_output(['media-ctl', '-p'], text=True)
        if 'ov5640 4-003c' not in topology:
            raise RuntimeError('The tested MX93 OV5640 camera was not found')
        return
    topology = subprocess.check_output(['media-ctl', '-p'], text=True)
    sensor = 'ov5640 2-003c'
    if sensor not in topology:
        raise RuntimeError('The tested MX95 CSI0 OV5640 camera was not found')
    subprocess.run(['media-ctl', '-l',
        f'"{sensor}":0 -> "csidev-4ad30000.csi":0 [1]'], check=True)
    pads = [(sensor, 0), ('csidev-4ad30000.csi', 0),
            ('4ac10000.syscon:formatter@20', 0), ('crossbar', 2)]
    pads.extend((f'mxc_isi.{index}', 0) for index in range(8))
    pads.append(('mxc_isi.0', 1))
    for entity, pad in pads:
        subprocess.run(['media-ctl', '-V',
            f'"{entity}":{pad} [fmt:UYVY8_1X16/1280x720 field:none]'],
            check=True)


def load_model(platform, task):
    suffix = 'vela' if platform == 'imx93' else 'neutron'
    filename = ('mobilenet' if task == 'classification' else 'ssd')
    delegate = ('ethosu' if platform == 'imx93' else 'neutron')
    startup_step(f'Loading {filename} and {delegate} delegate')
    interpreter = Interpreter(
        model_path=str(ROOT / 'model' / f'{filename}_{suffix}.tflite'),
        num_threads=1, experimental_delegates=[load_delegate(
            f'/usr/lib/lib{delegate}_delegate.so')])
    interpreter.allocate_tensors()
    source = interpreter.get_input_details()[0]
    outputs = interpreter.get_output_details()
    ops = interpreter._get_ops_details()
    custom = 'ethos-u' if platform == 'imx93' else 'NeutronGraph'
    if (source['dtype'] != np.uint8
            or not any(op['op_name'] == custom for op in ops)
            or not any(op['op_name'] == 'DELEGATE'
                       and source['index'] in op['inputs'] for op in ops)):
        raise RuntimeError('Expected compiled uint8 model delegated to its NPU')
    labels_file = 'classification-labels.txt' if task == 'classification' else (
        'detection-labels.txt' if platform == 'imx93' else 'coco-labels.txt')
    lines = (ROOT / 'model' / labels_file).read_text().splitlines()
    if task == 'detection' and platform == 'imx93':
        labels = {int(match[1]): match[2].strip() for line in lines
                  if (match := re.match(r'\s*(\d+)\s+(.+)', line))}
    elif task == 'detection':
        # NXP coco_labels.txt omits the background at output class zero.
        labels = dict(enumerate(lines, start=1))
    else:
        labels = dict(enumerate(lines))
    if task == 'classification' and len(labels) != outputs[0]['shape'][-1]:
        raise RuntimeError('Classification labels do not match model output')
    priors = None
    if task == 'detection' and platform == 'imx95':
        priors = np.loadtxt(ROOT / 'model/box-priors.txt')
        if priors.shape != (4, 1917) or len(labels) != 90:
            raise RuntimeError('Expected SSD-Lite anchors and 90 COCO labels')
    startup_step('Warming up the NPU with a model-sized frame')
    interpreter.set_tensor(source['index'], np.zeros(source['shape'], np.uint8))
    interpreter.invoke()
    return interpreter, source, outputs, labels, priors


def badge(frame, text, x, y, right=False):
    font, scale = cv2.FONT_HERSHEY_SIMPLEX, .6
    (width, height), baseline = cv2.getTextSize(text, font, scale, 1)
    if right:
        x -= width + 16
    x = max(0, min(x, frame.shape[1] - width - 16))
    bottom = min(frame.shape[0], y + height + baseline + 14)
    region = frame[y:bottom, x:x + width + 16]
    if region.size:
        cv2.addWeighted(region, .25, np.full_like(region, (23, 29, 34)),
                        .75, 0, region)
        cv2.putText(frame, text, (x + 8, y + height + 5), font, scale,
                    (240, 246, 248), 1, cv2.LINE_AA)


def overlay(frame, detections, labels, title, fps, ms, thermal, sensor,
            box_area=None):
    height, width = frame.shape[:2]
    box_area = box_area or (0, 0, width, height)
    for box, class_id, score in detections:
        left, top, right, bottom = display_box(box, box_area)
        color = COLORS[class_id % len(COLORS)]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2, cv2.LINE_AA)
        text = f'{labels.get(class_id, "object")}  {score:.0%}'
        badge(frame, text, left, max(0, top - 36))
    badge(frame, f'{fps:.1f} FPS  |  {ms:.1f} ms', width - 8, 8, right=True)
    badge(frame, title, 8, height - 36)
    value = thermal.read()
    badge(frame, f'{sensor} {value:.1f} C' if value is not None else
          f'{sensor} unavailable', width - 8, height - 36, right=True)


@demo_session()
def run(args):
    platform = board()
    interpreter, source, outputs, labels, priors = load_model(platform, args.task)
    size = (int(source['shape'][2]), int(source['shape'][1]))
    if args.video:
        path = Path(args.video).resolve()
        if not path.is_file():
            raise RuntimeError('Selected video does not exist')
        location = str(path).replace('\\', '\\\\').replace('"', '\\"')
        decoder = ('avidemux ! jpegdec' if platform == 'imx93' else 'decodebin')
        pipeline = f'filesrc location="{location}" ! {decoder} ! '
        if platform == 'imx95':
            runtime = Path(os.environ.setdefault('XDG_RUNTIME_DIR', '/run/user/0'))
            sockets = sorted(path for path in runtime.glob('wayland-*')
                             if path.is_socket())
            if not sockets:
                raise RuntimeError('MX95 GPU video conversion needs Wayland')
            os.environ.setdefault('WAYLAND_DISPLAY', sockets[0].name)
            os.environ.setdefault('GST_GL_PLATFORM', 'egl')
            os.environ.setdefault('GST_GL_WINDOW', 'wayland')
            os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
            pipeline += gpu_video_conversion()
    else:
        configure_camera(platform, args.camera)
        dimensions = ('format=YUY2,width=1280,height=720' if platform == 'imx95'
                      else 'width=640,height=480')
        pipeline = (f'v4l2src device={args.camera} ! '
                    f'video/x-raw,{dimensions} ! ')
    # A leaky queue BEFORE a clocked video sink discards the clip while it is
    # being decoded and leaves a future-timestamped final frame waiting. Keep
    # files clocked, and drop only late sink samples. Live cameras may leak.
    if not args.video:
        pipeline += 'queue leaky=downstream max-size-buffers=1 ! '
    pipeline += capture_tail(bool(args.video))
    startup_step('Opening video; waiting for the first frame')
    if args.video:
        from capture import VideoCapture
        cap = VideoCapture(pipeline)
        register_cleanup(cap.release)
    else:
        cap = managed_capture(pipeline)
    pacer = ThermalPacer()
    thermal = SoCTemperature(sensor_name=(
        'cpu-thermal' if platform == 'imx93' else 'a55-thermal'))
    started, frames = monotonic(), 0
    title = ('MobileNet V1' if args.task == 'classification' else
             'SSD MobileNet V1' if platform == 'imx93' else 'SSD-Lite V2')
    title += ' | ' + ('Ethos-U65' if platform == 'imx93' else 'Neutron')
    while not args.seconds or monotonic() - started < args.seconds:
        def stop_requested():
            return (bool(args.seconds and monotonic() - started >= args.seconds)
                    or (not args.headless and frames > 0
                        and cv2.waitKey(1) & 0xff == 27))

        if not pacer.wait(stop_requested):
            break
        ok, frame = cap.read()
        if not ok:
            if args.video and frames:
                break
            raise RuntimeError('Capture stopped delivering frames')
        rgb = cv2.cvtColor(cv2.resize(frame, size), cv2.COLOR_BGR2RGB)
        interpreter.set_tensor(source['index'], rgb[None])
        before = monotonic()
        interpreter.invoke()
        ms = (monotonic() - before) * 1000
        record_inference(ms / 1000)
        values = [interpreter.get_tensor(item['index']) for item in outputs]
        if not all(np.isfinite(value).all() for value in values):
            raise RuntimeError('Invalid model output')
        detections = []
        if args.task == 'detection':
            detections = (decode_postprocessed(values) if priors is None else
                          decode_ssdlite(values[0], values[1], priors))
        frames += 1
        if frames == 1:
            if not args.headless:
                cv2.namedWindow(title, cv2.WINDOW_NORMAL)
                if not args.windowed:
                    cv2.setWindowProperty(title, cv2.WND_PROP_FULLSCREEN,
                                          cv2.WINDOW_FULLSCREEN)
        if args.headless:
            if frames == 1:
                startup_step('Frames and NPU inference ready', ready=True)
            continue
        frame, box_area = display_view(frame)
        overlay(frame, detections, labels, title,
                frames / max(monotonic() - started, .001), ms, thermal, 'CPU',
                box_area)
        if args.task == 'classification':
            scores = values[0][0].astype(np.float32)
            scale, zero = outputs[0]['quantization']
            if scale:
                scores = (scores - zero) * scale
            for row, index in enumerate(np.argsort(scores)[-3:][::-1]):
                badge(frame, f'{labels[int(index)]}  {scores[index]:.0%}',
                      8, 8 + row * 38)
        cv2.imshow(title, frame)
        if frames == 1:
            startup_step('Frames and NPU inference ready', ready=True)
        if cv2.waitKey(1) & 0xff == 27:
            break
    if not frames:
        raise RuntimeError('No frames processed')
    print(f'Processed {frames} frames in {monotonic() - started:.2f} seconds',
          flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=['classification', 'detection'],
                        default='detection')
    parser.add_argument('--camera', default='/dev/video0')
    parser.add_argument('--video')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--windowed', action='store_true')
    parser.add_argument('--seconds', type=float, default=0)
    run(parser.parse_args())
