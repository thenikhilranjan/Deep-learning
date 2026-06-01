"""Crop raw RGB frames to the fixed size required for late fusion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import cv2


DEFAULT_CROP_WIDTH = 1250
DEFAULT_CROP_HEIGHT = 1000
DEFAULT_SHIFT_X = 12
DEFAULT_SHIFT_Y = 18
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


@dataclass
class RgbCropConfig:
    crop_width: int = DEFAULT_CROP_WIDTH
    crop_height: int = DEFAULT_CROP_HEIGHT
    shift_x: int = DEFAULT_SHIFT_X
    shift_y: int = DEFAULT_SHIFT_Y


@dataclass
class RgbCropReport:
    input_count: int = 0
    success_count: int = 0
    skipped_count: int = 0
    output_image_dir: Optional[Path] = None
    output_label_dir: Optional[Path] = None
    cropped_paths: List[Path] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)


def get_crop_coordinates(
    img_w: int,
    img_h: int,
    config: RgbCropConfig,
) -> Tuple[int, int, int, int]:
    if config.crop_width > img_w or config.crop_height > img_h:
        raise ValueError(
            f"Crop size {config.crop_width}x{config.crop_height} is larger than "
            f"image size {img_w}x{img_h}."
        )

    x_start = (img_w - config.crop_width) // 2 + config.shift_x
    y_start = (img_h - config.crop_height) // 2 + config.shift_y
    x_start = max(0, min(x_start, img_w - config.crop_width))
    y_start = max(0, min(y_start, img_h - config.crop_height))
    x_end = x_start + config.crop_width
    y_end = y_start + config.crop_height
    return x_start, y_start, x_end, y_end


def convert_label_after_crop(
    label_path: Path,
    output_label_path: Path,
    img_w: int,
    img_h: int,
    x_start: int,
    y_start: int,
    config: RgbCropConfig,
) -> None:
    new_lines: List[str] = []

    if not label_path.exists():
        output_label_path.write_text("")
        return

    with open(label_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            continue

        cls_id, x_c, y_c, box_w, box_h = parts
        x_c = float(x_c)
        y_c = float(y_c)
        box_w = float(box_w)
        box_h = float(box_h)

        x_center_px = x_c * img_w
        y_center_px = y_c * img_h
        box_w_px = box_w * img_w
        box_h_px = box_h * img_h

        x1 = x_center_px - box_w_px / 2
        y1 = y_center_px - box_h_px / 2
        x2 = x_center_px + box_w_px / 2
        y2 = y_center_px + box_h_px / 2

        x1_new = max(0, min(config.crop_width, x1 - x_start))
        y1_new = max(0, min(config.crop_height, y1 - y_start))
        x2_new = max(0, min(config.crop_width, x2 - x_start))
        y2_new = max(0, min(config.crop_height, y2 - y_start))

        new_box_w = x2_new - x1_new
        new_box_h = y2_new - y1_new
        if new_box_w <= 1 or new_box_h <= 1:
            continue

        new_x_center = ((x1_new + x2_new) / 2) / config.crop_width
        new_y_center = ((y1_new + y2_new) / 2) / config.crop_height
        new_w = new_box_w / config.crop_width
        new_h = new_box_h / config.crop_height

        new_lines.append(
            f"{cls_id} {new_x_center:.6f} {new_y_center:.6f} {new_w:.6f} {new_h:.6f}\n"
        )

    with open(output_label_path, "w") as f:
        f.writelines(new_lines)


def list_rgb_images(image_dir: Path) -> List[Path]:
    paths: List[Path] = []
    for ext in IMAGE_EXTENSIONS:
        paths.extend(image_dir.glob(f"*{ext}"))
        paths.extend(image_dir.glob(f"*{ext.upper()}"))
    return sorted(set(paths))


class RgbCropPreprocessor:
    """Crop raw RGB images (and optional YOLO labels) for multimodal fusion."""

    def __init__(self, config: Optional[RgbCropConfig] = None) -> None:
        self.config = config or RgbCropConfig()

    def process_folder(
        self,
        image_input_dir: Path,
        image_output_dir: Path,
        label_input_dir: Optional[Path] = None,
        label_output_dir: Optional[Path] = None,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
    ) -> RgbCropReport:
        image_input_dir = Path(image_input_dir)
        image_output_dir = Path(image_output_dir)
        image_output_dir.mkdir(parents=True, exist_ok=True)

        if label_output_dir is not None:
            label_output_dir = Path(label_output_dir)
            label_output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = list_rgb_images(image_input_dir)
        report = RgbCropReport(
            input_count=len(image_paths),
            output_image_dir=image_output_dir,
            output_label_dir=label_output_dir,
        )

        for idx, img_path in enumerate(image_paths, start=1):
            img = cv2.imread(str(img_path))
            if img is None:
                report.skipped_count += 1
                report.messages.append(f"Unreadable image: {img_path.name}")
                continue

            img_h, img_w = img.shape[:2]
            try:
                x_start, y_start, x_end, y_end = get_crop_coordinates(img_w, img_h, self.config)
            except ValueError as exc:
                report.skipped_count += 1
                report.messages.append(f"{img_path.name}: {exc}")
                continue

            cropped = img[y_start:y_end, x_start:x_end]
            output_img_path = image_output_dir / img_path.name
            cv2.imwrite(str(output_img_path), cropped)
            report.cropped_paths.append(output_img_path)
            report.success_count += 1

            if label_output_dir is not None:
                label_in = (label_input_dir or image_input_dir) / f"{img_path.stem}.txt"
                label_out = label_output_dir / f"{img_path.stem}.txt"
                convert_label_after_crop(
                    label_path=label_in,
                    output_label_path=label_out,
                    img_w=img_w,
                    img_h=img_h,
                    x_start=x_start,
                    y_start=y_start,
                    config=self.config,
                )

            if progress_cb is not None:
                progress_cb(idx, len(image_paths), img_path.name)

        return report


__all__ = [
    "RgbCropConfig",
    "RgbCropReport",
    "RgbCropPreprocessor",
    "get_crop_coordinates",
    "convert_label_after_crop",
    "list_rgb_images",
    "DEFAULT_CROP_WIDTH",
    "DEFAULT_CROP_HEIGHT",
    "DEFAULT_SHIFT_X",
    "DEFAULT_SHIFT_Y",
]
