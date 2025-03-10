# Copyright 2025 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

import os
from multiprocessing import cpu_count
from typing import Optional, List

import numpy as np
from tflite_runtime.interpreter import Interpreter as TFLiteInterpreter
from tflite_runtime.interpreter import load_delegate

from config import MODEL_NPU, DELEGATE_LIB


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
        if self.model == MODEL_NPU:
            ext_delegate_options = {}
            delegate = [load_delegate(DELEGATE_LIB, ext_delegate_options)]
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

    def get_output(self) -> np.ndarray:
        """
        Retrieves the model's output tensor.
        """
        return self.interpreter.get_tensor(self.output_details[0]["index"])[0]

    def set_input(self, input_data: np.ndarray) -> None:
        """
        Sets the input tensor for the model.
        """
        if not isinstance(input_data, np.ndarray):
            raise TypeError("Input data must be a numpy ndarray.")

        tensor_index = self.input_details[0]["index"]
        self.interpreter.set_tensor(tensor_index, input_data)

    def run_inference(self) -> None:
        """
        Runs inference using the TensorFlow Lite model.
        """
        self.interpreter.invoke()
