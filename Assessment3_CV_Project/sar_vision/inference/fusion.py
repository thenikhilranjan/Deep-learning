"""Late fusion of RGB and Thermal YOLO models.

This module is the package-level home of the late-fusion pipeline that used
to live in ``fusion_model.py`` at the project root. It exposes a
:class:`LateFusionRunner` that can fuse a single pair of images, a pair of
folders (matched by frame id) or a pair of videos (matched by frame index).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np


DEFAULT_RGB_SIZE: Tuple[int, int] = (1250, 1000)
DEFAULT_THERMAL_SIZE: Tuple[int, int] = (640, 512)
DEFAULT_CLASS_NAMES: Dict[int, str] = {0: "person"}


# ---------------------------------------------------------------------------
# Filename / matching helpers
# ---------------------------------------------------------------------------


def extract_frame_id(image_path) -> int:
    """Return the integer frame id encoded after the final underscore."""

    stem = Path(image_path).stem
    frame_str = stem.split("_")[-1]
    return int(frame_str)


def build_frame_index(image_dir: Path) -> Tuple[Dict[int, Path], List[Path]]:
    """Build a ``frame_id -> path`` index and a list of skipped files."""

    frame_index: Dict[int, Path] = {}
    skipped: List[Path] = []

    image_paths = sorted(
        list(image_dir.rglob("*.jpg"))
        + list(image_dir.rglob("*.jpeg"))
        + list(image_dir.rglob("*.png"))
    )

    for path in image_paths:
        try:
            frame_id = extract_frame_id(path)
        except ValueError:
            skipped.append(path)
            continue

        if frame_id in frame_index:
            skipped.append(path)
            continue

        frame_index[frame_id] = path

    return frame_index, skipped


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def compute_iou(box1: Sequence[float], box2: Sequence[float]) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def map_boxes_between_sizes(
    detections: List[dict],
    source_size: Tuple[int, int],
    target_size: Tuple[int, int],
) -> List[dict]:
    source_w, source_h = source_size
    target_w, target_h = target_size
    scale_x = target_w / source_w
    scale_y = target_h / source_h

    mapped: List[dict] = []
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        new_det = det.copy()
        new_det["box"] = [x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y]
        mapped.append(new_det)
    return mapped


def clip_boxes(detections: List[dict], image_size: Tuple[int, int]) -> List[dict]:
    w, h = image_size
    clipped: List[dict] = []
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w - 1))
        y2 = max(0, min(y2, h - 1))
        if x2 <= x1 or y2 <= y1:
            continue
        new_det = det.copy()
        new_det["box"] = [x1, y1, x2, y2]
        clipped.append(new_det)
    return clipped


# ---------------------------------------------------------------------------
# Drawing / IO helpers
# ---------------------------------------------------------------------------


def draw_detections(
    image: np.ndarray,
    detections: List[dict],
    class_names: Optional[Dict[int, str]] = None,
) -> np.ndarray:
    class_names = class_names or DEFAULT_CLASS_NAMES
    for det in detections:
        x1, y1, x2, y2 = map(int, det["box"])
        conf = det["conf"]
        cls_id = det["cls"]
        modalities = "+".join(det.get("modalities", [det.get("modality", "?")]))
        label = f"{class_names.get(cls_id, cls_id)} {conf:.2f} [{modalities}]"
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.putText(
            image,
            label,
            (x1, max(y1 - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    return image


def save_yolo_labels(
    detections: List[dict],
    output_path: Path,
    image_size: Tuple[int, int],
) -> None:
    w, h = image_size
    with open(output_path, "w") as f:
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            cls_id = det["cls"]
            conf = det["conf"]
            x_center = ((x1 + x2) / 2) / w
            y_center = ((y1 + y2) / 2) / h
            box_w = (x2 - x1) / w
            box_h = (y2 - y1) / h
            f.write(
                f"{cls_id} {x_center:.6f} {y_center:.6f} "
                f"{box_w:.6f} {box_h:.6f} {conf:.6f}\n"
            )


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class FusionResult:
    """Outputs for a single fused frame pair."""

    frame_id: int
    rgb_dets: List[dict]
    thermal_dets: List[dict]
    fused_dets_thermal_space: List[dict]
    fused_dets_rgb_space: List[dict]
    annotated_thermal: np.ndarray
    annotated_rgb: np.ndarray


@dataclass
class FusionFolderReport:
    """Aggregate report when fusing a whole folder or video pair."""

    output_dir: Path
    rgb_count: int = 0
    thermal_count: int = 0
    matched_pairs: int = 0
    missing_thermal: List[int] = field(default_factory=list)
    missing_rgb: List[int] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    per_frame: List[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class LateFusionRunner:
    """Run RGB and Thermal YOLO models and fuse their detections.

    The runner holds the two YOLO models in memory and exposes three entry
    points:

    - :meth:`fuse_pair` for a single image pair already in memory.
    - :meth:`run_folder_pair` for a folder of RGB-cropped images and a folder
      of thermal images matched by frame id (last ``_`` in the filename).
    - :meth:`run_video_pair` for an RGB and a thermal video matched by frame
      index.
    """

    def __init__(
        self,
        rgb_model_path: str,
        thermal_model_path: str,
        rgb_size: Tuple[int, int] = DEFAULT_RGB_SIZE,
        thermal_size: Tuple[int, int] = DEFAULT_THERMAL_SIZE,
        rgb_imgsz: int = 1280,
        thermal_imgsz: int = 640,
        rgb_conf: float = 0.25,
        thermal_conf: float = 0.25,
        iou_threshold: float = 0.35,
        rgb_weight: float = 1.0,
        thermal_weight: float = 1.0,
        class_names: Optional[Dict[int, str]] = None,
    ) -> None:
        from ultralytics import YOLO  # type: ignore

        self.rgb_model = YOLO(str(rgb_model_path))
        self.thermal_model = YOLO(str(thermal_model_path))
        self.rgb_size = rgb_size
        self.thermal_size = thermal_size
        self.rgb_imgsz = rgb_imgsz
        self.thermal_imgsz = thermal_imgsz
        self.rgb_conf = rgb_conf
        self.thermal_conf = thermal_conf
        self.iou_threshold = iou_threshold
        self.rgb_weight = rgb_weight
        self.thermal_weight = thermal_weight
        self.class_names = class_names or DEFAULT_CLASS_NAMES

    # -- low level -----------------------------------------------------

    def _run_yolo(self, model, image, imgsz, conf, modality) -> List[dict]:
        results = model.predict(source=image, imgsz=imgsz, conf=conf, verbose=False)[0]
        detections: List[dict] = []
        if results.boxes is None:
            return detections
        boxes = results.boxes.xyxy.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        for box, score, cls_id in zip(boxes, confs, classes):
            detections.append(
                {
                    "box": box.tolist(),
                    "conf": float(score),
                    "cls": int(cls_id),
                    "modality": modality,
                }
            )
        return detections

    def _fuse_detections(
        self,
        rgb_dets: List[dict],
        thermal_dets: List[dict],
    ) -> List[dict]:
        all_dets: List[dict] = []
        for det in rgb_dets:
            new_det = det.copy()
            new_det["weight"] = self.rgb_weight
            all_dets.append(new_det)
        for det in thermal_dets:
            new_det = det.copy()
            new_det["weight"] = self.thermal_weight
            all_dets.append(new_det)

        all_dets.sort(key=lambda d: d["conf"], reverse=True)

        fused: List[dict] = []
        used = [False] * len(all_dets)
        for i, det in enumerate(all_dets):
            if used[i]:
                continue
            group = [det]
            used[i] = True
            for j in range(i + 1, len(all_dets)):
                if used[j]:
                    continue
                other = all_dets[j]
                if det["cls"] != other["cls"]:
                    continue
                if compute_iou(det["box"], other["box"]) >= self.iou_threshold:
                    group.append(other)
                    used[j] = True

            weighted_box = np.zeros(4)
            total_weight = 0.0
            confs: List[float] = []
            modalities: List[str] = []
            for item in group:
                item_weight = item["conf"] * item["weight"]
                weighted_box += np.array(item["box"]) * item_weight
                total_weight += item_weight
                confs.append(item["conf"])
                modalities.append(item["modality"])

            fused_box = weighted_box / total_weight
            if len(set(modalities)) > 1:
                fused_conf = min(1.0, max(confs) + 0.10)
            else:
                fused_conf = max(confs)

            fused.append(
                {
                    "box": fused_box.tolist(),
                    "conf": float(fused_conf),
                    "cls": det["cls"],
                    "modalities": sorted(set(modalities)),
                }
            )
        return fused

    # -- public --------------------------------------------------------

    def fuse_pair(
        self,
        rgb_bgr: np.ndarray,
        thermal_bgr: np.ndarray,
        frame_id: int = 0,
    ) -> FusionResult:
        rgb_resized = cv2.resize(rgb_bgr, self.rgb_size, interpolation=cv2.INTER_LINEAR)
        thermal_resized = cv2.resize(
            thermal_bgr, self.thermal_size, interpolation=cv2.INTER_LINEAR
        )

        rgb_dets = self._run_yolo(
            self.rgb_model, rgb_resized, self.rgb_imgsz, self.rgb_conf, "rgb"
        )
        thermal_dets = self._run_yolo(
            self.thermal_model,
            thermal_resized,
            self.thermal_imgsz,
            self.thermal_conf,
            "thermal",
        )

        rgb_in_thermal = clip_boxes(
            map_boxes_between_sizes(rgb_dets, self.rgb_size, self.thermal_size),
            self.thermal_size,
        )
        thermal_dets = clip_boxes(thermal_dets, self.thermal_size)

        fused = clip_boxes(
            self._fuse_detections(rgb_in_thermal, thermal_dets),
            self.thermal_size,
        )

        fused_rgb_space = clip_boxes(
            map_boxes_between_sizes(fused, self.thermal_size, self.rgb_size),
            self.rgb_size,
        )

        annotated_thermal = draw_detections(thermal_resized.copy(), fused, self.class_names)
        annotated_rgb = draw_detections(rgb_resized.copy(), fused_rgb_space, self.class_names)

        return FusionResult(
            frame_id=frame_id,
            rgb_dets=rgb_dets,
            thermal_dets=thermal_dets,
            fused_dets_thermal_space=fused,
            fused_dets_rgb_space=fused_rgb_space,
            annotated_thermal=annotated_thermal,
            annotated_rgb=annotated_rgb,
        )

    def run_folder_pair(
        self,
        rgb_dir: Path,
        thermal_dir: Path,
        output_dir: Path,
        progress_cb=None,
    ) -> FusionFolderReport:
        rgb_dir = Path(rgb_dir)
        thermal_dir = Path(thermal_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        rgb_index, rgb_skipped = build_frame_index(rgb_dir)
        thermal_index, thermal_skipped = build_frame_index(thermal_dir)

        common = sorted(set(rgb_index) & set(thermal_index))
        missing_thermal = sorted(set(rgb_index) - set(thermal_index))
        missing_rgb = sorted(set(thermal_index) - set(rgb_index))

        report = FusionFolderReport(
            output_dir=output_dir,
            rgb_count=len(rgb_index),
            thermal_count=len(thermal_index),
            matched_pairs=len(common),
            missing_thermal=missing_thermal,
            missing_rgb=missing_rgb,
            skipped_files=[p.name for p in rgb_skipped + thermal_skipped],
        )

        for idx, frame_id in enumerate(common, start=1):
            rgb_path = rgb_index[frame_id]
            thermal_path = thermal_index[frame_id]
            rgb_img = cv2.imread(str(rgb_path))
            thermal_img = cv2.imread(str(thermal_path))
            if rgb_img is None or thermal_img is None:
                continue

            result = self.fuse_pair(rgb_img, thermal_img, frame_id=frame_id)
            self._write_outputs(result, output_dir)
            report.per_frame.append(
                {
                    "frame_id": frame_id,
                    "rgb_file": rgb_path.name,
                    "thermal_file": thermal_path.name,
                    "rgb_detections": len(result.rgb_dets),
                    "thermal_detections": len(result.thermal_dets),
                    "fused_detections": len(result.fused_dets_thermal_space),
                    "avg_conf": float(
                        np.mean([d["conf"] for d in result.fused_dets_thermal_space])
                    )
                    if result.fused_dets_thermal_space
                    else 0.0,
                }
            )
            if progress_cb is not None:
                progress_cb(idx, len(common), frame_id)

        return report

    def run_video_pair(
        self,
        rgb_video_path: Path,
        thermal_video_path: Path,
        output_dir: Path,
        max_frames: int = 300,
        progress_cb=None,
    ) -> FusionFolderReport:
        rgb_video_path = Path(rgb_video_path)
        thermal_video_path = Path(thermal_video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        rgb_cap = cv2.VideoCapture(str(rgb_video_path))
        thermal_cap = cv2.VideoCapture(str(thermal_video_path))

        report = FusionFolderReport(output_dir=output_dir)
        frame_id = 0
        try:
            while frame_id < max_frames:
                ok_r, rgb_frame = rgb_cap.read()
                ok_t, thermal_frame = thermal_cap.read()
                if not ok_r or not ok_t:
                    break
                frame_id += 1
                result = self.fuse_pair(rgb_frame, thermal_frame, frame_id=frame_id)
                self._write_outputs(result, output_dir)
                report.per_frame.append(
                    {
                        "frame_id": frame_id,
                        "rgb_file": f"{rgb_video_path.name}#{frame_id}",
                        "thermal_file": f"{thermal_video_path.name}#{frame_id}",
                        "rgb_detections": len(result.rgb_dets),
                        "thermal_detections": len(result.thermal_dets),
                        "fused_detections": len(result.fused_dets_thermal_space),
                        "avg_conf": float(
                            np.mean([d["conf"] for d in result.fused_dets_thermal_space])
                        )
                        if result.fused_dets_thermal_space
                        else 0.0,
                    }
                )
                if progress_cb is not None:
                    progress_cb(frame_id, max_frames, frame_id)
        finally:
            rgb_cap.release()
            thermal_cap.release()

        report.rgb_count = frame_id
        report.thermal_count = frame_id
        report.matched_pairs = frame_id
        return report

    def _write_outputs(self, result: FusionResult, output_dir: Path) -> None:
        fid = result.frame_id
        cv2.imwrite(str(output_dir / f"fused_thermal_frame_{fid:06d}.jpg"), result.annotated_thermal)
        cv2.imwrite(str(output_dir / f"fused_rgb_frame_{fid:06d}.jpg"), result.annotated_rgb)
        save_yolo_labels(
            result.fused_dets_thermal_space,
            output_dir / f"fused_frame_{fid:06d}.txt",
            self.thermal_size,
        )


__all__ = [
    "LateFusionRunner",
    "FusionResult",
    "FusionFolderReport",
    "extract_frame_id",
    "build_frame_index",
    "compute_iou",
    "map_boxes_between_sizes",
    "clip_boxes",
    "draw_detections",
    "save_yolo_labels",
    "DEFAULT_RGB_SIZE",
    "DEFAULT_THERMAL_SIZE",
]
