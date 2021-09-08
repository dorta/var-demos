# Copyright 2021 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

import cv2
import numpy as np
from PIL import Image
from tflite_runtime.interpreter import Interpreter

input_image = cv2.imread("data/zero.png")
input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
input_image = cv2.resize(input_image, (28, 28), interpolation = cv2.INTER_LINEAR)
input_image = np.expand_dims(np.array(input_image, dtype=np.float32) / 255.0, 0)

interpreter = Interpreter(model_path="model/mnist.tflite")
interpreter.allocate_tensors()
interpreter.set_tensor(interpreter.get_input_details()[0]["index"], input_image)

interpreter.invoke()
result = interpreter.tensor(interpreter.get_output_details()[0]["index"])()[0]

digit = np.argmax(result)
print(f"Predicted Digit: {digit}\nConfidence: {result[digit]}")