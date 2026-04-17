"""Rendering utilities for detections and previews."""

from __future__ import annotations

from typing import Iterable, Mapping

import cv2
import numpy as np


def to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert OpenCV-style BGR or grayscale arrays into RGB arrays."""
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def draw_detections(
    image: np.ndarray,
    detections: Iterable[Mapping[str, object]],
    color: tuple = (0, 255, 0),
) -> np.ndarray:
    """Draw detection boxes and labels on a copy of the input image."""
    canvas = image.copy()
    if canvas.ndim == 2:
        canvas = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)

    for detection in detections:
        x_min = int(detection["x_min"])
        y_min = int(detection["y_min"])
        x_max = int(detection["x_max"])
        y_max = int(detection["y_max"])
        label = str(detection["label"])
        confidence = float(detection["confidence"])
        text = f"{label} {confidence:.2f}"

        cv2.rectangle(canvas, (x_min, y_min), (x_max, y_max), color, 2)
        cv2.putText(
            canvas,
            text,
            (x_min, max(16, y_min - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    return canvas
