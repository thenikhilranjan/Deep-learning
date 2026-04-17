"""YOLO dataset preparation and optional training helpers."""

from __future__ import annotations

import random
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from sar_vision.config import get_settings
from sar_vision.data.manifest import load_manifest
from sar_vision.data.models import DatasetReport, SampleRecord


class YoloTrainingManager:
    """Prepare modality-specific YOLO datasets and run optional training."""

    def __init__(self, manifest_path: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.settings.ensure_runtime_dirs()
        self.manifest_path = manifest_path or self.settings.dataset_manifest_path

    def prepare_dataset(
        self,
        *,
        modality: str = "thermal",
        output_dir: Optional[Path] = None,
        class_names: Optional[Sequence[str]] = None,
        split_ratios: Sequence[float] = (0.7, 0.15, 0.15),
        seed: int = 42,
        use_symlinks: bool = True,
    ) -> Path:
        """Create a YOLO-ready folder structure from the dataset manifest."""
        if modality == "paired":
            raise NotImplementedError(
                "Paired RGB-thermal training needs a fusion-specific pipeline and is not "
                "yet exported as a standard YOLO dataset."
            )

        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Dataset manifest not found at {self.manifest_path}. Run the validator first."
            )

        class_names = list(class_names or self.settings.default_class_names)
        report = load_manifest(self.manifest_path)
        filtered_samples = self._filter_samples(report, modality)
        if not filtered_samples:
            raise ValueError(
                f"No usable samples found for modality '{modality}'. Check the dataset manifest."
            )

        output_dir = output_dir or self.settings.cache_dir / "yolo_dataset" / modality
        images_root = output_dir / "images"
        labels_root = output_dir / "labels"
        data_yaml_path = output_dir / "data.yaml"

        if output_dir.exists():
            shutil.rmtree(output_dir)
        for split in ("train", "val", "test"):
            (images_root / split).mkdir(parents=True, exist_ok=True)
            (labels_root / split).mkdir(parents=True, exist_ok=True)

        split_map = self._assign_splits(filtered_samples, split_ratios=split_ratios, seed=seed)
        for sample in filtered_samples:
            split = split_map[sample.sequence_name]
            image_path = Path(sample.image_path or "")
            label_path = Path(sample.label_path) if sample.label_path else None

            target_image = images_root / split / image_path.name
            target_label = labels_root / split / f"{sample.sample_stem}.txt"

            self._link_or_copy(image_path, target_image, use_symlinks=use_symlinks)
            if label_path and label_path.exists():
                self._link_or_copy(label_path, target_label, use_symlinks=use_symlinks)
            else:
                target_label.write_text("", encoding="utf-8")

        data_yaml_path.write_text(
            self._build_data_yaml(output_dir, class_names=class_names), encoding="utf-8"
        )
        return data_yaml_path

    def train(
        self,
        *,
        data_yaml_path: Path,
        model_name: str = "yolov8n.pt",
        epochs: int = 20,
        image_size: Optional[int] = None,
        project_dir: Optional[Path] = None,
    ) -> Dict[str, object]:
        """Train a YOLO model if Ultralytics is available."""
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Ultralytics is not installed. Add it to the environment to enable training."
            ) from exc

        image_size = image_size or self.settings.default_image_size
        project_dir = project_dir or self.settings.models_dir
        project_dir.mkdir(parents=True, exist_ok=True)

        model = YOLO(model_name)
        results = model.train(
            data=str(data_yaml_path),
            epochs=epochs,
            imgsz=image_size,
            project=str(project_dir),
            name=data_yaml_path.parent.name,
        )
        return {
            "model_name": model_name,
            "save_dir": str(results.save_dir),
            "epochs": epochs,
            "image_size": image_size,
        }

    def _filter_samples(self, report: DatasetReport, modality: str) -> List[SampleRecord]:
        usable = [
            sample
            for sample in report.samples
            if sample.image_exists and (modality == "all" or sample.modality == modality)
        ]
        usable.sort(key=lambda sample: (sample.sequence_name, sample.sample_stem))
        return usable

    def _assign_splits(
        self,
        samples: Sequence[SampleRecord],
        *,
        split_ratios: Sequence[float],
        seed: int,
    ) -> Dict[str, str]:
        grouped: Dict[str, List[SampleRecord]] = defaultdict(list)
        for sample in samples:
            grouped[sample.sequence_name].append(sample)

        sequences = list(grouped.keys())
        random.Random(seed).shuffle(sequences)

        train_ratio, val_ratio, _ = split_ratios
        total_sequences = len(sequences)
        train_cutoff = max(1, int(total_sequences * train_ratio))
        val_cutoff = max(train_cutoff + 1, int(total_sequences * (train_ratio + val_ratio)))

        split_map: Dict[str, str] = {}
        for index, sequence_name in enumerate(sequences):
            if index < train_cutoff:
                split_map[sequence_name] = "train"
            elif index < val_cutoff:
                split_map[sequence_name] = "val"
            else:
                split_map[sequence_name] = "test"
        return split_map

    def _link_or_copy(self, source: Path, target: Path, *, use_symlinks: bool) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            target.unlink()

        if use_symlinks:
            try:
                target.symlink_to(source)
                return
            except OSError:
                pass

        shutil.copy2(source, target)

    def _build_data_yaml(self, output_dir: Path, *, class_names: Sequence[str]) -> str:
        names_list = ", ".join(f"'{name}'" for name in class_names)
        return "\n".join(
            [
                f"path: {output_dir}",
                "train: images/train",
                "val: images/val",
                "test: images/test",
                f"names: [{names_list}]",
                "",
            ]
        )
