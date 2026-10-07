# Copyright 2025 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import os

import cv2
import numpy as np
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

from tflite_runtime.interpreter import Interpreter, load_delegate

from utils import (
    Framerate, Timer, put_info_on_frame, load_labels, debug_profile,
    COMBINATIONS,
    profile, show_available_combinations
)
from runtime import demo_session, register_cleanup, ThermalPacer, warm_up_model, startup_step

EXT_DELEGATE_PATH = "/usr/lib/libvx_delegate.so"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def open_gst_pipeline(source, debug=False):
    with debug_profile("Gst.init and parse pipeline", debug):
        Gst.init(None)
        escaped_source = source.replace('\\', '\\\\').replace('"', '\\"')
        pipeline = Gst.parse_launch(
            f'filesrc location="{escaped_source}" ! decodebin ! '
            "imxvideoconvert_g2d ! "
            "video/x-raw,format=RGBx ! appsink name=sink emit-signals=true "
            "max-buffers=1 drop=true sync=true wait-on-eos=false"
        )
    with debug_profile("Gst get sink element", debug):
        sink = pipeline.get_by_name("sink")
    with debug_profile("Gst pipeline set_state PLAYING", debug):
        register_cleanup(pipeline.set_state, Gst.State.NULL)
        pipeline.set_state(Gst.State.PLAYING)
    return pipeline, sink


@profile
def gst_read_frame(sink, debug=False):
    with debug_profile("sink.emit(try-pull-sample)", debug):
        sample = sink.emit("try-pull-sample", 2 * Gst.SECOND)
    if not sample:
        bus = sink.get_parent().get_bus()
        message = bus.pop_filtered(Gst.MessageType.ERROR)
        if message is not None:
            error, details = message.parse_error()
            raise RuntimeError(f'Video pipeline failed: {error}; {details}')
        if sink.get_property('eos'):
            return None
        raise TimeoutError('Video pipeline stopped delivering frames')

    with debug_profile("sample.get_buffer", debug):
        buf = sample.get_buffer()
    with debug_profile("sample.get_caps", debug):
        caps = sample.get_caps()
    h = caps.get_structure(0).get_value('height')
    w = caps.get_structure(0).get_value('width')

    with debug_profile("buf.extract_dup", debug):
        data = buf.extract_dup(0, buf.get_size())
    expected_size = h * w * 4

    if buf.get_size() == expected_size:
        with debug_profile("np.frombuffer reshape (full)", debug):
            frame = np.frombuffer(data, np.uint8).reshape((h, w, 4))
    else:
        with debug_profile("data[:expected_size] slice", debug):
            cropped_data = data[:expected_size]
        with debug_profile("np.frombuffer reshape (cropped)", debug):
            frame = np.frombuffer(cropped_data, np.uint8).reshape((h, w, 4))

    with debug_profile("cv2.cvtColor RGBA2RGB", debug):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

    return frame


@profile
def load_interpreter(model_path, debug=False):
    with debug_profile("Interpreter + load_delegate", debug):
        interpreter = Interpreter(
            model_path=model_path,
            experimental_delegates=[load_delegate(EXT_DELEGATE_PATH)]
        )
    with debug_profile("allocate_tensors", debug):
        interpreter.allocate_tensors()
    return interpreter


@profile
def run_inference(interpreter, input_data, debug=False):
    with debug_profile("interpreter.set_tensor", debug):
        input_details = interpreter.get_input_details()
        interpreter.set_tensor(input_details[0]['index'], input_data)
    with debug_profile("interpreter.invoke", debug):
        interpreter.invoke()


@profile
def get_output_tensor(interpreter, index, debug=False):
    with debug_profile("get_output_tensor", debug):
        output_details = interpreter.get_output_details()
        return interpreter.get_tensor(output_details[index]['index'])


@profile
def parse_results(interpreter, threshold=0.5, debug=False):
    with debug_profile("parse_results tensors squeeze", debug):
        boxes = np.squeeze(get_output_tensor(interpreter, 0, debug))
        classes = np.squeeze(get_output_tensor(interpreter, 1, debug))
        scores = np.squeeze(get_output_tensor(interpreter, 2, debug))

    results = []
    with debug_profile("parse loop", debug):
        for i, score in enumerate(np.atleast_1d(scores)):
            if score > threshold:
                results.append({
                    "box": boxes[i],
                    "class": int(classes[i]),
                    "score": float(score)
                })
    return results

@profile
@demo_session()
def main(args):
    if args.combination < 1 or args.combination > len(COMBINATIONS):
        print("Invalid combination number. Choose between 1 and",
              len(COMBINATIONS))
        return

    video, video_res, display, display_res, mode = (
        COMBINATIONS[args.combination - 1]
    )
    if args.video:
        video = args.video
    elif not os.path.isabs(video):
        video = os.path.join(SCRIPT_DIR, video)

    if not os.path.isfile(video):
        raise FileNotFoundError(
            f"Video not found: {video}. Use --video to select an input file."
        )

    print(f"Selected Combination #{args.combination}: Video={video}, "
          f"VideoRes={video_res}, Display={display}, "
          f"DisplayRes={display_res}, Mode={mode}")

    labels = load_labels(args.label)
    interpreter = load_interpreter(args.model, args.debug)
    warm_up_model(interpreter)
    input_details = interpreter.get_input_details()
    model_height, model_width = input_details[0]['shape'][1:3]

    pipeline, sink = open_gst_pipeline(video, args.debug)
    timer = Timer()
    framerate = Framerate()
    frame_count = 0
    detected_frames = 0
    detection_count = 0

    window_created = False
    pacer = ThermalPacer()

    while True:
        poll_stop = (lambda: False) if args.headless else (
            lambda: cv2.waitKey(1) == 27
        )
        if not pacer.wait(poll_stop):
            break
        frame = gst_read_frame(sink, args.debug)
        if frame is None:
            break

        resized_input = cv2.resize(frame, (model_width, model_height))
        input_data = np.expand_dims(resized_input, axis=0).astype(np.uint8)

        with timer.timeit():
            run_inference(interpreter, input_data, args.debug)

        results = parse_results(interpreter, debug=args.debug)
        frame_count += 1
        detection_count += len(results)
        if results:
            detected_frames += 1
        fps = framerate.update()
        frame = put_info_on_frame(
            frame, results, timer.time, labels, args.model, video, fps,
            display_res
        )

        if not args.headless:
            if not window_created:
                cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)
                if mode == "fullscreen":
                    cv2.setWindowProperty(
                        "Detection", cv2.WND_PROP_FULLSCREEN,
                        cv2.WINDOW_FULLSCREEN
                    )
                window_created = True
            cv2.imshow("Detection", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            if frame_count == 1:
                cv2.waitKey(1)
                startup_step('Frames and NPU inference ready', ready=True)
            if cv2.waitKey(1) == 27:
                break

    print(
        f"Processed {frame_count} frames; detected {detection_count} objects "
        f"across {detected_frames} frames."
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model',
        default=os.path.join(
            SCRIPT_DIR,
            "assets/model/ssd_mobilenet_v1_1_default_1.tflite"
        )
    )
    parser.add_argument(
        '--label',
        default=os.path.join(
            SCRIPT_DIR,
            "assets/model/labels_ssd_mobilenet_v1.txt"
        )
    )
    parser.add_argument(
        '--combination',
        type=int,
        help="Combination number to run (1-18)"
    )
    parser.add_argument(
        '--video',
        help="Video file to use instead of the selected preset's input"
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help="Run inference without opening an OpenCV display window"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable detailed profiling output"
    )

    args = parser.parse_args()

    import utils
    utils.PROFILE_ENABLED = args.debug

    if args.combination is None:
        show_available_combinations()

    main(args)
