#!/usr/bin/env python3

# Copyright 2021-2025 Variscite Ltd.
# SPDX-License-Identifier: Variscite Proprietary License

# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import os
import re

def read_labels(labels_file):
    """
    Reads a labels file and returns a dictionary mapping integers to label names.
    Expects lines in the form: <int> <label>
    """
    if not os.path.isfile(labels_file):
        raise ValueError("Must pass a labels file")
    if not labels_file.endswith(".txt"):
        raise TypeError(f"Expects {labels_file} to be a text file")

    labels_dict = {}
    pattern = re.compile(r'\s*(\d+)\s*[:\s]\s*(.+)')

    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                num, text = match.groups()
                labels_dict[int(num)] = text.strip()

    return labels_dict
