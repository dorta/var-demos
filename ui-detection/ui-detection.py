#!/usr/bin/env python3

# Copyright 2021-2025 Variscite Ltd.
# SPDX-License-Identifier: Variscite Proprietary License

# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import argparse
import threading
from time import sleep

import cv2
import gi
gi.require_versions({'Gdk': "3.0", 'GdkPixbuf': "2.0", 'Gtk': "3.0"})
from gi.repository.GdkPixbuf import Colorspace, Pixbuf
from gi.repository import Gdk, GLib, Gtk
import numpy as np

from config import *
from interpreter import Interpreter
from multimedia import *
from utils import read_labels


global counter, stop
counter = DEMO_DURATION
stop = False


class RealTimeDetection(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.fullscreen()
        self.set_border_width(2)

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        provider.load_from_data(INTERFACE_CSS)

        self.pixbuf = None

        self.detection_list = ML_SSD_LABELS_LIST.copy()
        self.labels = read_labels(ML_LABELS)
        self.interpreter = None

        self.camera_pipeline = get_camera_pipeline(CAMERA_DEFAULT_PATH, *CAMERA_DEFAULT_RES)
        self.cap = cv2.VideoCapture(self.camera_pipeline, cv2.CAP_GSTREAMER)

        event_box = Gtk.EventBox()
        event_box.connect("button_press_event",self.on_interaction)
        self.add(event_box)

        horizontal_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        event_box.add(horizontal_box)

        scrolled_window = Gtk.ScrolledWindow()
        horizontal_box.pack_start(scrolled_window, True, True, 0)

        vertical_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_window.add(vertical_box)

        for label in self.detection_list:
            toggle_button = Gtk.CheckButton(label=f'{label}')
            toggle_button.set_active(True)
            toggle_button.connect('toggled', self.on_object_toggled, label)
            vertical_box.pack_start(toggle_button, True, True, 0)

        self.displayed_image = Gtk.Image()
        horizontal_box.pack_start(self.displayed_image, True, True, 0)

        img = cv2.imread(LOADING_CAMERA_IMAGE)
        self.set_displayed_image(img)

        self.start_interpreter()
        self.run_application()

    def on_object_toggled(self, button, obj):
        global counter
        if counter < 15:
            counter = 15

        if button.get_active():
            if obj not in self.detection_list:
                self.detection_list.append(obj)
        else:
            if obj in self.detection_list:
                self.detection_list.remove(obj)

    def on_interaction(self, widget, event):
        global counter
        if counter < 15:
            counter = 15


    def image_detection(self):
        while True:
            if not stop:
                """Capture a frame from the camera and update the GUI."""
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera.")
                    break

                frame = cv2.flip(frame, 1)

                input_data = preprocess_image(frame, self.interpreter)

                self.interpreter.set_input(input_data)
                self.interpreter.run_inference()

                positions = self.interpreter.get_output(0, squeeze=True)
                classes = self.interpreter.get_output(1, squeeze=True)
                scores = self.interpreter.get_output(2, squeeze=True)

                result = []
                for idx, score in enumerate(scores):
                    if score > 0.5 and (self.labels[classes[idx]] in self.detection_list):
                        result.append({'pos': positions[idx], '_id': classes[idx]})

                output_frame = overlay_image(frame=frame, top_result=result, labels=self.labels,)

                GLib.idle_add(self.set_displayed_image, output_frame)


    def time_counter(self):
        global counter, stop

        while True:
            if counter > 0:
                sleep(1)
                counter -= 1
            else:
                stop = True
                self.hide()

                run_video(args)

                img = cv2.imread(LOADING_INTERPRETER_IMAGE)
                GLib.idle_add(self.set_displayed_image, img)
                self.show_all()
                self.start_interpreter()

                counter = DEMO_DURATION
                stop = False

    def set_displayed_image(self, image):
        image = cv2.resize(image, (640,480))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        height, width = image.shape[:2]
        arr = np.ndarray.tobytes(image)
        self.pixbuf = Pixbuf.new_from_data(arr, Colorspace.RGB, False, 8,
                                           width - 10, height - 10,
                                           width * 3, None, None)
        self.displayed_image.set_from_pixbuf(self.pixbuf)

    def start_interpreter(self):
        self.interpreter = Interpreter(model=ML_MODEL_NPU)

    def run_application(self):
        time_thread = threading.Thread(target=self.time_counter)
        time_thread.daemon = True
        time_thread.start()

        detection_thread = threading.Thread(target=self.image_detection)
        detection_thread.daemon = True
        detection_thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--som", required=True, help="SOM type: 'dart' or 'var-som'")
    args = parser.parse_args()

    capture_devices = get_cameras()

    if capture_devices:
        app = RealTimeDetection()
        app.connect('delete-event', Gtk.main_quit)
        app.show_all()
        Gtk.main()
    else:
        sleep(5)
        while True:
            run_video(args)
