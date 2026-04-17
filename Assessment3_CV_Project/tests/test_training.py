from pathlib import Path

from PIL import Image

from sar_vision.data.manifest import save_manifest
from sar_vision.data.models import DatasetReport, SampleRecord, SequenceSummary
from sar_vision.training import YoloTrainingManager


def test_prepare_dataset_builds_yolo_workspace(tmp_path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    image_a = image_dir / "frame_a.png"
    image_b = image_dir / "frame_b.png"
    Image.new("L", (32, 32), color=160).save(image_a)
    Image.new("L", (32, 32), color=90).save(image_b)

    label_a = image_dir / "frame_a.txt"
    label_a.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    report = DatasetReport(
        dataset_root=str(tmp_path / "datasets"),
        generated_at="2026-03-31T00:00:00+00:00",
        sequence_count=1,
        image_count=2,
        label_count=1,
        matched_pairs=1,
        missing_images=0,
        missing_labels=1,
        sequences=[
            SequenceSummary(
                dataset_name="WiSARDv1",
                sequence_name="demo_IR_sequence",
                modality="thermal",
                image_count=2,
                label_count=1,
                matched_pairs=1,
                missing_images=0,
                missing_labels=1,
                total_boxes=1,
            )
        ],
        samples=[
            SampleRecord(
                dataset_name="WiSARDv1",
                sequence_name="demo_IR_sequence",
                sample_stem="frame_a",
                modality="thermal",
                image_path=str(image_a),
                label_path=str(label_a),
                image_exists=True,
                label_exists=True,
                width=32,
                height=32,
                box_count=1,
            ),
            SampleRecord(
                dataset_name="WiSARDv1",
                sequence_name="demo_IR_sequence",
                sample_stem="frame_b",
                modality="thermal",
                image_path=str(image_b),
                label_path=None,
                image_exists=True,
                label_exists=False,
                width=32,
                height=32,
                box_count=0,
            ),
        ],
    )

    manifest_path = tmp_path / "dataset_manifest.json"
    save_manifest(report, manifest_path)

    manager = YoloTrainingManager(manifest_path=manifest_path)
    data_yaml = manager.prepare_dataset(
        modality="thermal",
        output_dir=tmp_path / "yolo_workspace",
        use_symlinks=False,
    )

    assert data_yaml.exists()
    assert (tmp_path / "yolo_workspace" / "images").exists()
    assert (tmp_path / "yolo_workspace" / "labels").exists()
    assert (
        tmp_path / "yolo_workspace" / "labels" / "train" / "frame_b.txt"
    ).read_text(encoding="utf-8") == ""
