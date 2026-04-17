"""Reusable preprocessing transforms for RGB and thermal imagery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import cv2
import numpy as np


@dataclass
class PreprocessOptions:
    """Runtime configuration for image preprocessing."""

    normalize_thermal: bool = False
    apply_clahe: bool = False
    denoise: bool = False
    denoise_method: str = "gaussian"
    resize_to: Tuple[int, int] | None = None
    grayscale: bool = False


def ensure_uint8(image: np.ndarray) -> np.ndarray:
    """Normalize image dtype to uint8 for OpenCV operations."""
    if image.dtype == np.uint8:
        return image
    clipped = np.clip(image, 0, 255)
    return clipped.astype(np.uint8)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR or RGB image to grayscale if needed."""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thermal_normalization(image: np.ndarray) -> np.ndarray:
    """Stretch thermal intensities into the full display range."""
    grayscale = to_grayscale(ensure_uint8(image))
    return cv2.normalize(grayscale, None, 0, 255, cv2.NORM_MINMAX)


def clahe_enhancement(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    """Improve local contrast using CLAHE."""
    working = ensure_uint8(image)
    if working.ndim == 2:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        return clahe.apply(working)

    lab = cv2.cvtColor(working, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    enhanced = clahe.apply(l_channel)
    merged = cv2.merge((enhanced, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def denoise_image(image: np.ndarray, method: str = "gaussian") -> np.ndarray:
    """Reduce noise with a conservative blur filter."""
    working = ensure_uint8(image)
    if method == "median":
        return cv2.medianBlur(working, 3)
    if method == "bilateral":
        return cv2.bilateralFilter(working, 5, 25, 25)
    return cv2.GaussianBlur(working, (3, 3), 0)


def resize_image(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Resize an image to a fixed width-height tuple."""
    width, height = size
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)


def tile_image(
    image: np.ndarray, tile_size: Tuple[int, int] = (640, 640), overlap: float = 0.2
) -> List[Dict[str, object]]:
    """Split a large image into overlapping tiles for small-object experiments."""
    tile_width, tile_height = tile_size
    step_x = max(1, int(tile_width * (1.0 - overlap)))
    step_y = max(1, int(tile_height * (1.0 - overlap)))
    height, width = image.shape[:2]
    tiles: List[Dict[str, object]] = []

    for top in range(0, max(1, height - tile_height + 1), step_y):
        for left in range(0, max(1, width - tile_width + 1), step_x):
            bottom = min(top + tile_height, height)
            right = min(left + tile_width, width)
            tile = image[top:bottom, left:right]
            tiles.append(
                {
                    "tile": tile,
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                }
            )

    if not tiles:
        tiles.append(
            {"tile": image.copy(), "left": 0, "top": 0, "right": width, "bottom": height}
        )

    return tiles


def apply_preprocessing(
    image: np.ndarray, options: PreprocessOptions
) -> Tuple[np.ndarray, List[str]]:
    """Apply the configured preprocessing pipeline and report the steps used."""
    output = ensure_uint8(image.copy())
    applied_steps: List[str] = []

    if options.normalize_thermal:
        output = thermal_normalization(output)
        applied_steps.append("thermal_normalization")

    if options.apply_clahe:
        output = clahe_enhancement(output)
        applied_steps.append("clahe")

    if options.denoise:
        output = denoise_image(output, method=options.denoise_method)
        applied_steps.append(f"denoise:{options.denoise_method}")

    if options.grayscale:
        output = to_grayscale(output)
        applied_steps.append("grayscale")

    if options.resize_to:
        output = resize_image(output, options.resize_to)
        applied_steps.append(f"resize:{options.resize_to[0]}x{options.resize_to[1]}")

    return output, applied_steps
