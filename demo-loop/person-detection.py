#!/usr/bin/env python3

# Copyright 2025-2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import time
import cv2
import numpy as np
import gi
import threading

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GdkPixbuf

from config import *
from interpreter import Interpreter
from multimedia import *

class ObjectDetectionApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Persons Detection")
        self.fullscreen()
        self.inference_time = 0
        self.count = 0
        self.display_dimensions = get_display_dimensions()

        self.image = Gtk.Image()
        self.add(self.image)

        self.interpreter = Interpreter(model=MODEL_NPU)

        self.camera_pipeline = get_camera_pipeline(LIBCAMERA_DEFAULT_PATH, *CAMERA_DEFAULT_RES)
        self.cap = cv2.VideoCapture(self.camera_pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            print("Error: Could not open video stream.")
            exit()

        self.frame_skip = 3
        self.frame_counter = 0
        self.run_application()


    def update_frame(self):
        while True:
            """Capture a frame from the camera and update the GUI."""
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame from camera.")
                break

            if self.frame_counter % self.frame_skip == 0:
                boxes, scores, class_ids = self.run_detection(frame)

            # Draw detection boxes on frame
            for (x1, y1, x2, y2), score, class_id in zip(boxes[:5], scores, class_ids):
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            self.overlay_text_with_border(frame)

            self.frame_counter += 1

            GLib.idle_add(self.set_frame_on_pixbuf, frame)


    def run_detection(self, frame, confidence_threshold=0.4, nms_threshold=0.4):
        image_shape0, image_shape1 = frame.shape[:2]

        input_data = preprocess_image(frame, self.interpreter)
        self.interpreter.set_input(input_data)

        inf_start_time = time.time()
        self.interpreter.run_inference()
        inf_time = time.time() - inf_start_time
        self.count += 1
        self.inference_time = self.inference_time + (inf_time - self.inference_time) / self.count

        output_data = self.interpreter.get_output()

        if self.interpreter.input_dtype == np.int8:
            output_data = (output_data.astype(np.float32) - self.interpreter.output_zero_point) * self.interpreter.output_scale

        valid_indices = output_data[4] > confidence_threshold
        if not np.any(valid_indices):
            return [], [], []

        selected_boxes = output_data[:4, valid_indices].T
        scores = output_data[4, valid_indices]
        class_ids = output_data[5, valid_indices].astype(int)

        boxes = np.column_stack([
            (selected_boxes[:, 0] - selected_boxes[:, 2] / 2) * image_shape1,
            (selected_boxes[:, 1] - selected_boxes[:, 3] / 2) * image_shape0,
            (selected_boxes[:, 0] + selected_boxes[:, 2] / 2) * image_shape1,
            (selected_boxes[:, 1] + selected_boxes[:, 3] / 2) * image_shape0
        ]).astype(int)

        # Apply Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), confidence_threshold, nms_threshold)

        if len(indices) > 0:
            indices = indices.flatten()
            boxes = [boxes[i].tolist() for i in indices]
            scores = [scores[i] for i in indices]
            class_ids = [class_ids[i] for i in indices]

        return boxes, scores, class_ids

    def overlay_text_with_border(self, frame):
        left_text = f"Inference Time: {self.inference_time * 1000:.2f}ms"
        right_text = "YOLOv8"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        font_thickness = 2

        text_color = (255, 255, 255)  # White
        border_color = (0, 0, 0)  # Black

        # Define bottom text position
        y_text = frame.shape[0] - 10  # 10 pixels above the bottom edge
        # Define left text position
        x_left_text = 10

        # Define right text position
        (right_text_width, right_text_height), baseline = cv2.getTextSize(right_text, font, font_scale, font_thickness)
        x_right_text = frame.shape[1] - 10 - right_text_width

        # Draw text multiple times slightly shifted to create a border effect
        offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2)]

        for dx, dy in offsets:
            cv2.putText(frame, left_text, (x_left_text + dx, y_text + dy), font, font_scale, border_color, font_thickness + 2, cv2.LINE_AA)
            cv2.putText(frame, right_text, (x_right_text + dx, y_text + dy), font, font_scale, border_color, font_thickness + 2, cv2.LINE_AA)

        cv2.putText(frame, left_text, (x_left_text, y_text), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
        cv2.putText(frame, right_text, (x_right_text, y_text), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

    def set_frame_on_pixbuf(self, frame):
        frame = cv2.resize(frame, self.display_dimensions, interpolation=cv2.INTER_NEAREST)

        height, width, channels = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert BGR to RGB

        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            frame_rgb.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            False, 8, width, height,
            width * channels,
        )

        self.image.set_from_pixbuf(pixbuf)

    def run_application(self):
        thread = threading.Thread(target=self.update_frame)
        thread.daemon = True
        thread.start()

    def on_destroy(self, widget):
        self.cap.release()
        Gtk.main_quit()


if __name__ == "__main__":
    app = ObjectDetectionApp()
    app.connect("destroy", app.on_destroy)
    app.show_all()
    Gtk.main()
