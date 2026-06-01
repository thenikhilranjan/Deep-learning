"""Inference backends for the Search and Rescue project."""

from .service import DetectionService
from .fusion import (
    LateFusionRunner,
    FusionResult,
    FusionFolderReport,
    extract_frame_id,
    build_frame_index,
    DEFAULT_RGB_SIZE,
    DEFAULT_THERMAL_SIZE,
)

__all__ = [
    "DetectionService",
    "LateFusionRunner",
    "FusionResult",
    "FusionFolderReport",
    "extract_frame_id",
    "build_frame_index",
    "DEFAULT_RGB_SIZE",
    "DEFAULT_THERMAL_SIZE",
]
