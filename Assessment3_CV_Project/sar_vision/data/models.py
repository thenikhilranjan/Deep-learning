"""Dataclasses used by dataset validation and manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BoundingBox:
    """Normalized YOLO-format bounding box."""

    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class SampleRecord:
    """Single sample in the dataset manifest."""

    dataset_name: str
    sequence_name: str
    sample_stem: str
    modality: str
    image_path: Optional[str]
    label_path: Optional[str]
    image_exists: bool
    label_exists: bool
    width: Optional[int]
    height: Optional[int]
    box_count: int
    split: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SequenceSummary:
    """Aggregated statistics for a sequence folder."""

    dataset_name: str
    sequence_name: str
    modality: str
    image_count: int
    label_count: int
    matched_pairs: int
    missing_images: int
    missing_labels: int
    total_boxes: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetReport:
    """Validation output for the full dataset tree."""

    dataset_root: str
    generated_at: str
    sequence_count: int
    image_count: int
    label_count: int
    matched_pairs: int
    missing_images: int
    missing_labels: int
    sequences: List[SequenceSummary] = field(default_factory=list)
    samples: List[SampleRecord] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_root": self.dataset_root,
            "generated_at": self.generated_at,
            "sequence_count": self.sequence_count,
            "image_count": self.image_count,
            "label_count": self.label_count,
            "matched_pairs": self.matched_pairs,
            "missing_images": self.missing_images,
            "missing_labels": self.missing_labels,
            "sequences": [sequence.to_dict() for sequence in self.sequences],
            "samples": [sample.to_dict() for sample in self.samples],
            "issues": self.issues,
        }
