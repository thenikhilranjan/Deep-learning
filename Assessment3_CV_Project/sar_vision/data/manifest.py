"""Persistence helpers for dataset manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import DatasetReport, SampleRecord, SequenceSummary


def save_manifest(report: DatasetReport, output_path: Path) -> Path:
    """Write a dataset report to disk as formatted JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return output_path


def load_manifest(path: Path) -> DatasetReport:
    """Load a previously saved dataset report."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    sequences = [
        SequenceSummary(**sequence_payload)
        for sequence_payload in payload.get("sequences", [])
    ]
    samples = [
        SampleRecord(**sample_payload) for sample_payload in payload.get("samples", [])
    ]
    return DatasetReport(
        dataset_root=payload["dataset_root"],
        generated_at=payload["generated_at"],
        sequence_count=payload["sequence_count"],
        image_count=payload["image_count"],
        label_count=payload["label_count"],
        matched_pairs=payload["matched_pairs"],
        missing_images=payload["missing_images"],
        missing_labels=payload["missing_labels"],
        sequences=sequences,
        samples=samples,
        issues=payload.get("issues", []),
    )


def sequence_rows(report: DatasetReport) -> List[Dict[str, Any]]:
    """Flatten sequence summaries for table rendering."""
    return [sequence.to_dict() for sequence in report.sequences]


def sample_rows(report: DatasetReport) -> List[Dict[str, Any]]:
    """Flatten sample rows for table rendering."""
    return [sample.to_dict() for sample in report.samples]
