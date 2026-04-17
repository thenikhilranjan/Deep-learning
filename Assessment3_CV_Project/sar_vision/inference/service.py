"""Inference services for heuristic and model-based person detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from sar_vision.preprocessing import PreprocessOptions, apply_preprocessing
from sar_vision.ui import draw_detections


@dataclass
class DetectorConfig:
    """Configuration for selecting a detection backend."""

    backend: str = "auto"
    confidence_threshold: float = 0.25
    model_path: Optional[Path] = None
    min_area_ratio: float = 0.0005


class DetectionService:
    """Run inference using either a classical thermal detector or YOLO."""

    def run(
        self,
        image: np.ndarray,
        *,
        modality: str = "thermal",
        preprocess_options: Optional[PreprocessOptions] = None,
        detector_config: Optional[DetectorConfig] = None,
    ) -> Dict[str, object]:
        preprocess_options = preprocess_options or PreprocessOptions()
        detector_config = detector_config or DetectorConfig()

        processed_image, preprocessing_steps = apply_preprocessing(image, preprocess_options)
        detections: List[Dict[str, object]] = []
        backend_used = detector_config.backend

        if detector_config.backend in {"auto", "yolo"} and detector_config.model_path:
            try:
                detections = self._run_yolo(
                    processed_image,
                    model_path=detector_config.model_path,
                    confidence_threshold=detector_config.confidence_threshold,
                )
                backend_used = "yolo"
            except Exception:
                if detector_config.backend == "yolo":
                    raise

        if not detections:
            detections = self._run_hotspot_detector(
                processed_image,
                modality=modality,
                min_area_ratio=detector_config.min_area_ratio,
            )
            backend_used = "thermal_hotspot"

        annotated = draw_detections(processed_image, detections)
        return {
            "backend_used": backend_used,
            "detections": detections,
            "processed_image": processed_image,
            "annotated_image": annotated,
            "preprocessing_steps": preprocessing_steps,
        }

    def _run_yolo(
        self,
        image: np.ndarray,
        *,
        model_path: Path,
        confidence_threshold: float,
    ) -> List[Dict[str, object]]:
        from ultralytics import YOLO  # type: ignore

        model = YOLO(str(model_path))
        results = model.predict(image, conf=confidence_threshold, verbose=False)

        detections: List[Dict[str, object]] = []
        for result in results:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                x_min, y_min, x_max, y_max = [int(value) for value in box.xyxy[0].tolist()]
                confidence = float(box.conf[0].item())
                detections.append(
                    {
                        "label": names.get(class_id, str(class_id)),
                        "confidence": confidence,
                        "x_min": x_min,
                        "y_min": y_min,
                        "x_max": x_max,
                        "y_max": y_max,
                        "alert_level": "high" if confidence >= 0.75 else "medium",
                    }
                )
        return detections

    def _run_hotspot_detector(
        self,
        image: np.ndarray,
        *,
        modality: str,
        min_area_ratio: float,
    ) -> List[Dict[str, object]]:
        """Find bright thermal-like regions as a fallback detector."""
        grayscale = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        normalized = cv2.normalize(grayscale, None, 0, 255, cv2.NORM_MINMAX)
        blurred = cv2.GaussianBlur(normalized, (5, 5), 0)
        _, threshold = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.dilate(cleaned, kernel, iterations=2)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        height, width = grayscale.shape[:2]
        minimum_area = max(20, int(height * width * min_area_ratio))

        detections: List[Dict[str, object]] = []
        for contour in contours:
            x_min, y_min, box_width, box_height = cv2.boundingRect(contour)
            area = box_width * box_height
            if area < minimum_area:
                continue

            region = normalized[y_min : y_min + box_height, x_min : x_min + box_width]
            confidence = float(np.mean(region) / 255.0)
            detections.append(
                {
                    "label": "person_candidate" if modality == "thermal" else "target_candidate",
                    "confidence": confidence,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_min + box_width,
                    "y_max": y_min + box_height,
                    "alert_level": "high" if confidence >= 0.75 else "medium",
                }
            )

        detections.sort(key=lambda item: item["confidence"], reverse=True)
        return detections
