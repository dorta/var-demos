#!/usr/bin/env python3

# Copyright 2021-2025 Variscite Ltd.
# SPDX-License-Identifier: Variscite Proprietary License

# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import argparse
import os
import cv2
import numpy as np
import gi

import threading
import subprocess
from time import sleep

gi.require_version('Gst', '1.0')
from gi.repository import Gst

from tflite_runtime.interpreter import Interpreter, load_delegate

from utils import (
    Timer, put_info_on_frame, load_labels, debug_profile, COMBINATIONS,
    profile, show_available_combinations
)

EXT_DELEGATE_PATH = "/usr/lib/libvx_delegate.so"

stop = False

def open_gst_pipeline(source):
    with debug_profile("Gst.init and parse pipeline", args.debug):
        Gst.init(None)
        pipeline = Gst.parse_launch(
            f"filesrc location={source} ! decodebin ! imxvideoconvert_g2d ! "
            "video/x-raw,format=RGBx ! appsink name=sink emit-signals=true "
            "sync=false"
        )
    with debug_profile("Gst get sink element", args.debug):
        sink = pipeline.get_by_name("sink")
    with debug_profile("Gst pipeline set_state PLAYING", args.debug):
        pipeline.set_state(Gst.State.PLAYING)
    return pipeline, sink


@profile
def gst_read_frame(sink):
    with debug_profile("sink.emit(pull-sample)", args.debug):
        sample = sink.emit("pull-sample")
    if not sample:
        return None

    with debug_profile("sample.get_buffer", args.debug):
        buf = sample.get_buffer()
    with debug_profile("sample.get_caps", args.debug):
        caps = sample.get_caps()
    h = caps.get_structure(0).get_value('height')
    w = caps.get_structure(0).get_value('width')

    with debug_profile("buf.extract_dup", args.debug):
        data = buf.extract_dup(0, buf.get_size())
    expected_size = h * w * 4

    if buf.get_size() == expected_size:
        with debug_profile("np.frombuffer reshape (full)", args.debug):
            frame = np.frombuffer(data, np.uint8).reshape((h, w, 4))
    else:
        with debug_profile("data[:expected_size] slice", args.debug):
            cropped_data = data[:expected_size]
        with debug_profile("np.frombuffer reshape (cropped)", args.debug):
            frame = np.frombuffer(cropped_data, np.uint8).reshape((h, w, 4))

    with debug_profile("cv2.cvtColor RGBA2RGB", args.debug):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

    return frame


@profile
def load_interpreter(model_path):
    with debug_profile("Interpreter + load_delegate", args.debug):
        interpreter = Interpreter(
            model_path=model_path,
            experimental_delegates=[load_delegate(EXT_DELEGATE_PATH)]
        )
    with debug_profile("allocate_tensors", args.debug):
        interpreter.allocate_tensors()
    return interpreter


@profile
def run_inference(interpreter, input_data):
    with debug_profile("interpreter.set_tensor", args.debug):
        input_details = interpreter.get_input_details()
        interpreter.set_tensor(input_details[0]['index'], input_data)
    with debug_profile("interpreter.invoke", args.debug):
        interpreter.invoke()


@profile
def get_output_tensor(interpreter, index):
    with debug_profile("get_output_tensor", args.debug):
        output_details = interpreter.get_output_details()
        return interpreter.get_tensor(output_details[index]['index'])


@profile
def parse_results(interpreter, threshold=0.5):
    with debug_profile("parse_results tensors squeeze", args.debug):
        boxes = np.squeeze(get_output_tensor(interpreter, 0))
        classes = np.squeeze(get_output_tensor(interpreter, 1))
        scores = np.squeeze(get_output_tensor(interpreter, 2))

    results = []
    with debug_profile("parse loop", args.debug):
        for i, score in enumerate(np.atleast_1d(scores)):
            if score > threshold:
                results.append({
                    "box": boxes[i],
                    "class": int(classes[i]),
                    "score": float(score)
                })
    return results

@profile
def main(args):
    global stop

    if args.som == "dart":
        unboxing_video = "/opt/assets/unboxing/DART-MX8M-PLUS.mp4"
    elif args.som == "var-som":
        unboxing_video = "/opt/assets/unboxing/VAR-SOM-MX8M-PLUS.mp4"
    else:
        print("[ERROR] Invalid --som argument.")
        return

    def start_video_demo():
        if args.combination < 1 or args.combination > len(COMBINATIONS):
            print("Invalid combination number. Choose between 1 and",
                  len(COMBINATIONS))
            return

        video, video_res, display, display_res, mode = (
            COMBINATIONS[args.combination - 1]
        )
        print(f"Selected Combination #{args.combination}: Video={video}, "
              f"VideoRes={video_res}, Display={display}, "
              f"DisplayRes={display_res}, Mode={mode}")

        labels = load_labels(args.label)
        interpreter = load_interpreter(args.model)
        input_details = interpreter.get_input_details()
        model_height, model_width = input_details[0]['shape'][1:3]

        pipeline, sink = open_gst_pipeline(video)
        timer = Timer()

        if mode == "fullscreen":
            cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Detection", cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN)
        else:
            cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)

        while True:
            if stop:
                break

            frame = gst_read_frame(sink)
            if frame is None:
                break

            resized_input = cv2.resize(frame, (model_width, model_height))
            input_data = np.expand_dims(resized_input, axis=0).astype(np.uint8)

            with timer.timeit():
                run_inference(interpreter, input_data)

            results = parse_results(interpreter)
            frame = put_info_on_frame(frame, results, timer.time, labels,
                                      args.model, video)

            if mode == "fullscreen" and frame.shape[1] != display_res[0]:
                frame = cv2.resize(frame, display_res)

            cv2.imshow("Detection", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) == 27:
                break

        pipeline.set_state(Gst.State.NULL)
        cv2.destroyAllWindows()

    def loop():
        global stop
        while True:
            stop = False
            start_video_demo()
            stop = True
            screen_freeze = subprocess.Popen(
                ['evtest', '--grab', '/dev/input/event2'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            try:
                cmd = (
                    f'gst-launch-1.0 playbin '
                    f'uri=file://{unboxing_video} '
                    'video-sink="waylandsink window-width=800 window-height=480"'
                )
                subprocess.run(cmd, shell=True, check=True)
            finally:
                screen_freeze.kill()
            sleep(1)

    loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model',
        default="/opt/assets/model/ssd_mobilenet_v1_1_default_1.tflite"
    )
    parser.add_argument(
        '--label',
        default="/opt/assets/model/labels_ssd_mobilenet_v1.txt"
    )
    parser.add_argument(
        '--combination',
        type=int,
        help="Combination number to run (1-18)"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable detailed profiling output"
    )
    parser.add_argument(
        '--som',
        required=True,
        choices=["dart", "var-som"],
        help="SoM type: dart or var-som"
    )

    args = parser.parse_args()

    import utils
    utils.PROFILE_ENABLED = args.debug

    if args.combination is None:
        show_available_combinations()

    main(args)
