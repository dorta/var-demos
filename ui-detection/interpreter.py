#!/usr/bin/env python3

# Copyright 2021-2025 Variscite Ltd.
# SPDX-License-Identifier: Variscite Proprietary License

# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import os
from multiprocessing import cpu_count
from typing import Optional, List

import numpy as np
from tflite_runtime.interpreter import Interpreter as TFLiteInterpreter
from tflite_runtime.interpreter import load_delegate

from config import ML_MODEL_NPU, ML_DELEGATE_LIB


class Interpreter:
    """
    Wrapper around TensorFlow Lite Interpreter for handling model inference.
    """
    def __init__(self, model: Optional[str] = None, num_threads: int = 1):
        if not model or not os.path.isfile(model):
            raise ValueError("Must pass a valid model file path.")

        if not model.endswith(".tflite"):
            raise TypeError(f"Expected '{model}' to be a '.tflite' file.")

        if not isinstance(num_threads, int) or num_threads < 1:
            raise ValueError("num_threads must be a positive integer.")

        if num_threads > cpu_count():
            raise ValueError(f"num_threads cannot be greater than {cpu_count()}.")

        self.model = model

        # Load delegate if using NPU model
        if self.model == ML_MODEL_NPU:
            ext_delegate_options = {}
            delegate = [load_delegate(ML_DELEGATE_LIB, ext_delegate_options)]
        else:
            delegate = None

        # Initialize the TensorFlow Lite Interpreter
        self.interpreter = TFLiteInterpreter(
            model_path=self.model,
            experimental_delegates=delegate,
            num_threads=num_threads
        )

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Extract input and output tensor properties
        self.input_shape = tuple(self.input_details[0]["shape"][1:3])
        self.input_dtype = self.input_details[0]["dtype"]
        self.input_scale, self.input_zero_point = self.input_details[0]["quantization"]
        self.output_scale, self.output_zero_point = self.output_details[0]["quantization"]

    def get_output(self, index: int, squeeze: bool = False) -> np.ndarray:
        """
        Get the result after running the inference.

        :param index: Index of the result.
        :param squeeze: Determines if the result should be squeezed or not.
        :return: Result tensor. If 'squeeze' is True, dimensions of size 1 are removed.
        :raises IndexError: If the provided index is out of range.
        """
        if index >= len(self.output_details):
            raise IndexError("Index out of range in output_details")

        tensor = self.interpreter.get_tensor(self.output_details[index]['index'])

        if squeeze:
            return np.squeeze(tensor)
        return tensor

    def set_input(self, image: np.ndarray) -> None:
        """
        Set the image/frame into the input tensor to be inferred.

        :param image: Image to be inferred.
        :raises TypeError: If image is not an ndarray.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("Image must be a numpy ndarray.")
        tensor_index = self.input_details[0]['index']
        self.interpreter.set_tensor(tensor_index, image)

    def run_inference(self) -> None:
        """
        Runs inference using the TensorFlow Lite model.
        """
        self.interpreter.invoke()
