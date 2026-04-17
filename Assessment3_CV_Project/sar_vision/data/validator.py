"""Dataset validation and manifest generation for local WiSARD data."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from PIL import Image

from sar_vision.config import IMAGE_EXTENSIONS, LABEL_EXTENSIONS, get_settings

from .manifest import save_manifest
from .models import BoundingBox, DatasetReport, SampleRecord, SequenceSummary


class DatasetValidator:
    """Validate a local dataset tree and produce a reusable manifest."""

    def __init__(self, dataset_root: Optional[Path] = None) -> None:
        settings = get_settings()
        settings.ensure_runtime_dirs()
        self.settings = settings
        self.dataset_root = (dataset_root or settings.datasets_dir).resolve()

    def validate(self, write_outputs: bool = True) -> DatasetReport:
        """Scan the dataset tree and return a full report."""
        if not self.dataset_root.exists():
            report = DatasetReport(
                dataset_root=str(self.dataset_root),
                generated_at=self._timestamp(),
                sequence_count=0,
                image_count=0,
                label_count=0,
                matched_pairs=0,
                missing_images=0,
                missing_labels=0,
                issues=[f"Dataset root does not exist: {self.dataset_root}"],
            )
            if write_outputs:
                self._write_summary(report)
                save_manifest(report, self.settings.dataset_manifest_path)
            return report

        sequences = self._find_sequence_dirs(self.dataset_root)
        if not sequences:
            report = DatasetReport(
                dataset_root=str(self.dataset_root),
                generated_at=self._timestamp(),
                sequence_count=0,
                image_count=0,
                label_count=0,
                matched_pairs=0,
                missing_images=0,
                missing_labels=0,
                issues=[f"No sequence folders with labels or images found under {self.dataset_root}"],
            )
            if write_outputs:
                self._write_summary(report)
                save_manifest(report, self.settings.dataset_manifest_path)
            return report

        sequence_summaries: List[SequenceSummary] = []
        sample_records: List[SampleRecord] = []

        for sequence_dir in sequences:
            sequence_summary, samples = self._scan_sequence(sequence_dir)
            sequence_summaries.append(sequence_summary)
            sample_records.extend(samples)

        report = DatasetReport(
            dataset_root=str(self.dataset_root),
            generated_at=self._timestamp(),
            sequence_count=len(sequence_summaries),
            image_count=sum(sequence.image_count for sequence in sequence_summaries),
            label_count=sum(sequence.label_count for sequence in sequence_summaries),
            matched_pairs=sum(sequence.matched_pairs for sequence in sequence_summaries),
            missing_images=sum(sequence.missing_images for sequence in sequence_summaries),
            missing_labels=sum(sequence.missing_labels for sequence in sequence_summaries),
            sequences=sequence_summaries,
            samples=sample_records,
            issues=self._build_issues(sequence_summaries, sample_records),
        )

        if write_outputs:
            save_manifest(report, self.settings.dataset_manifest_path)
            self._write_summary(report)

        return report

    def _find_sequence_dirs(self, dataset_root: Path) -> List[Path]:
        sequence_dirs: List[Path] = []
        for path in sorted(dataset_root.rglob("*")):
            if not path.is_dir():
                continue
            file_children = [child for child in path.iterdir() if child.is_file()]
            if any(child.suffix.lower() in IMAGE_EXTENSIONS | LABEL_EXTENSIONS for child in file_children):
                sequence_dirs.append(path)
        return sequence_dirs

    def _scan_sequence(self, sequence_dir: Path) -> Tuple[SequenceSummary, List[SampleRecord]]:
        image_files: Dict[str, Path] = {}
        label_files: Dict[str, Path] = {}

        for file_path in sorted(sequence_dir.iterdir()):
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            if suffix in IMAGE_EXTENSIONS:
                image_files[file_path.stem] = file_path
            elif suffix in LABEL_EXTENSIONS:
                label_files[file_path.stem] = file_path

        stems = sorted(set(image_files) | set(label_files))
        samples: List[SampleRecord] = []
        total_boxes = 0
        modality = self.infer_modality(sequence_dir.name)
        dataset_name = self._dataset_name_for(sequence_dir)

        for stem in stems:
            image_path = image_files.get(stem)
            label_path = label_files.get(stem)
            width, height = self._safe_image_size(image_path) if image_path else (None, None)
            box_count = 0
            if label_path:
                box_count = len(self.parse_yolo_labels(label_path))
                total_boxes += box_count

            samples.append(
                SampleRecord(
                    dataset_name=dataset_name,
                    sequence_name=sequence_dir.name,
                    sample_stem=stem,
                    modality=modality,
                    image_path=str(image_path) if image_path else None,
                    label_path=str(label_path) if label_path else None,
                    image_exists=image_path is not None,
                    label_exists=label_path is not None,
                    width=width,
                    height=height,
                    box_count=box_count,
                )
            )

        image_count = len(image_files)
        label_count = len(label_files)
        matched_pairs = sum(1 for sample in samples if sample.image_exists and sample.label_exists)
        missing_images = sum(1 for sample in samples if sample.label_exists and not sample.image_exists)
        missing_labels = sum(1 for sample in samples if sample.image_exists and not sample.label_exists)

        summary = SequenceSummary(
            dataset_name=dataset_name,
            sequence_name=sequence_dir.name,
            modality=modality,
            image_count=image_count,
            label_count=label_count,
            matched_pairs=matched_pairs,
            missing_images=missing_images,
            missing_labels=missing_labels,
            total_boxes=total_boxes,
        )
        return summary, samples

    def _dataset_name_for(self, sequence_dir: Path) -> str:
        try:
            return sequence_dir.relative_to(self.dataset_root).parts[0]
        except (ValueError, IndexError):
            return self.dataset_root.name

    def _build_issues(
        self, sequences: Iterable[SequenceSummary], samples: Iterable[SampleRecord]
    ) -> List[str]:
        issues: List[str] = []
        sequence_list = list(sequences)
        sample_list = list(samples)
        if not sequence_list:
            issues.append("No usable sequences were found.")
            return issues

        if all(sequence.image_count == 0 for sequence in sequence_list):
            issues.append("No image files were detected. The local dataset currently looks label-only.")
        if all(sequence.label_count == 0 for sequence in sequence_list):
            issues.append("No label files were detected.")

        modality_counts = Counter(sequence.modality for sequence in sequence_list)
        if modality_counts.get("rgb", 0) == 0:
            issues.append("No RGB sequences were detected from local naming patterns.")
        if modality_counts.get("thermal", 0) == 0:
            issues.append("No thermal sequences were detected from local naming patterns.")
        if modality_counts.get("paired", 0) == 0:
            issues.append("No paired RGB-thermal sequences were detected from local naming patterns.")

        label_only_samples = sum(
            1 for sample in sample_list if sample.label_exists and not sample.image_exists
        )
        if label_only_samples:
            issues.append(
                f"{label_only_samples} samples have labels but no matching image file in the same folder."
            )

        return issues

    def _write_summary(self, report: DatasetReport) -> None:
        payload = {
            "dataset_root": report.dataset_root,
            "generated_at": report.generated_at,
            "sequence_count": report.sequence_count,
            "image_count": report.image_count,
            "label_count": report.label_count,
            "matched_pairs": report.matched_pairs,
            "missing_images": report.missing_images,
            "missing_labels": report.missing_labels,
            "issues": report.issues,
        }
        self.settings.dataset_summary_path.write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def infer_modality(self, sequence_name: str) -> str:
        """Infer sequence modality from the directory name."""
        tokens = {
            token for token in re.split(r"[^A-Z0-9]+", sequence_name.upper()) if token
        }
        if tokens & {"PAIR", "PAIRED", "SYNC", "MULTI", "FUSION"}:
            return "paired"
        if tokens & {"IR", "THERM", "THERMAL", "LWIR"}:
            return "thermal"
        if tokens & {"RGB", "VIS", "VISIBLE", "EO"}:
            return "rgb"
        return "unknown"

    @staticmethod
    def parse_yolo_labels(label_path: Path) -> List[BoundingBox]:
        """Parse a YOLO-format label file into bounding boxes."""
        boxes: List[BoundingBox] = []
        for raw_line in label_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                continue
            class_id, x_center, y_center, width, height = parts
            boxes.append(
                BoundingBox(
                    class_id=int(float(class_id)),
                    x_center=float(x_center),
                    y_center=float(y_center),
                    width=float(width),
                    height=float(height),
                )
            )
        return boxes

    @staticmethod
    def _safe_image_size(image_path: Path) -> Tuple[Optional[int], Optional[int]]:
        try:
            with Image.open(image_path) as image:
                width, height = image.size
            return width, height
        except Exception:
            return None, None

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()


def main() -> None:
    """Allow quick manifest generation from the command line."""
    validator = DatasetValidator()
    report = validator.validate(write_outputs=True)
    summary = {
        "dataset_root": report.dataset_root,
        "sequence_count": report.sequence_count,
        "image_count": report.image_count,
        "label_count": report.label_count,
        "matched_pairs": report.matched_pairs,
        "missing_images": report.missing_images,
        "missing_labels": report.missing_labels,
        "issues": report.issues,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
