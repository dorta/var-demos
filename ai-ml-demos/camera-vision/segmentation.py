# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause
"""DeepLabV3 semantic masks for people and vehicles, not instance tracking."""

import cv2
import numpy as np

PERSON = 15
VEHICLES = (2, 6, 7, 14, 19)  # bicycle, bus, car, motorbike, train (PASCAL VOC)


def prepare_segmentation_input(rgb, source):
    if source['dtype'] != np.float32:
        raise ValueError('This DeepLab artifact expects normalized FLOAT32 RGB')
    return ((rgb.astype(np.float32) - 127.5) / 127.5)[None]


def decode_segmentation(scores):
    scores = np.asarray(scores)
    if scores.ndim != 4 or scores.shape[0] != 1 or scores.shape[-1] != 21:
        raise ValueError('Expected DeepLab scores [1,height,width,21]')
    if not np.isfinite(scores).all():
        raise ValueError('Non-finite segmentation scores')
    return np.argmax(scores[0], axis=-1).astype(np.uint8)


def read_segmentation(interpreter, output):
    # The 513x513x21 FLOAT32 scores occupy about 21 MiB. Use a short-lived
    # view rather than copying them each frame. Only the independent class
    # mask leaves this function; no tensor view survives the next invoke.
    scores = interpreter.tensor(output['index'])()
    return decode_segmentation(scores)


def paint_segmentation(frame, classes, area, opacity=.45):
    """Paint only the viewport; panels and letterbox bars stay untouched."""
    import vision_overlay as ui
    if not 0 <= opacity <= 1:
        raise ValueError('Mask opacity must be between zero and one')
    x, y, width, height = area
    mask = cv2.resize(classes, (width, height), interpolation=cv2.INTER_NEAREST)
    region = frame[y:y + height, x:x + width]
    people = mask == PERSON
    vehicles = np.isin(mask, VEHICLES)
    for selected, label in ((people, 'person'), (vehicles, 'car')):
        if selected.any():
            color = np.asarray(ui.color_for(label), np.float32)
            region[selected] = np.rint(region[selected] * (1 - opacity) +
                                      color * opacity).astype(np.uint8)
    return float(people.mean()), float(vehicles.mean())


def legend(frame):
    import vision_overlay as ui
    ui.panel(frame, 10, ui.FIELD_TOP, 225, 78)
    for row, (title, name) in enumerate((('People', 'person'), ('Vehicles', 'car'))):
        y = ui.FIELD_TOP + 11 + row * 32
        cv2.rectangle(frame, (22, y), (36, y + 14), ui.color_for(name), -1)
        cv2.putText(frame, title, (46, y + 14), ui.FONT, .6, ui.TEXT, 1, cv2.LINE_AA)


def load_segmentation_model(root, platform):
    from tflite_runtime.interpreter import Interpreter, load_delegate, OpResolverType
    from runtime import startup_step
    if platform not in ('imx8mplus', 'imx93'):
        raise RuntimeError('DeepLab on MX95 requires a converter matching its '
                           'Neutron driver; the 3.1.3 artifact is not enabled on 3.1.2')
    filename = 'deeplabv3_vela.tflite' if platform == 'imx93' else 'deeplabv3.tflite'
    delegate = 'ethosu' if platform == 'imx93' else 'vx'
    startup_step(f'Loading DeepLabV3 and {delegate} delegate')
    interpreter = Interpreter(model_path=str(root / 'model' / filename),
        num_threads=2,
        experimental_op_resolver_type=OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES,
        experimental_delegates=[load_delegate(f'/usr/lib/lib{delegate}_delegate.so')])
    interpreter.allocate_tensors()
    source = interpreter.get_input_details()[0]
    outputs = interpreter.get_output_details()
    ops = interpreter._get_ops_details()
    if (tuple(source['shape']) != (1, 513, 513, 3)
            or source['dtype'] != np.float32 or len(outputs) != 1
            or tuple(outputs[0]['shape']) != (1, 513, 513, 21)
            or outputs[0]['dtype'] != np.float32
            or not any(op['op_name'] == 'DELEGATE' for op in ops)):
        raise RuntimeError('Expected DeepLab with 513x513 RGB input and NPU delegation')
    if platform == 'imx93' and not any(op['op_name'] == 'ethos-u' for op in ops):
        raise RuntimeError('DeepLab was not compiled for Ethos-U65')
    startup_step('Warming up DeepLab; some operators also run on the CPU')
    interpreter.set_tensor(source['index'], np.zeros(source['shape'], np.float32))
    interpreter.invoke()
    decode_segmentation(interpreter.get_tensor(outputs[0]['index']))
    return interpreter, source, outputs, {}, None
