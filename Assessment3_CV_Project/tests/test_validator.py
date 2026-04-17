from pathlib import Path

from PIL import Image

from sar_vision.data.validator import DatasetValidator


def test_validator_detects_matches_and_gaps(tmp_path):
    dataset_root = tmp_path / "datasets"
    sequence_dir = dataset_root / "WiSARDv1" / "demo_VIS_sequence"
    sequence_dir.mkdir(parents=True)

    image_path = sequence_dir / "frame_001.png"
    Image.new("L", (32, 32), color=180).save(image_path)
    (sequence_dir / "frame_001.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    second_image_path = sequence_dir / "frame_002.png"
    Image.new("L", (32, 32), color=100).save(second_image_path)

    orphan_label = sequence_dir / "frame_003.txt"
    orphan_label.write_text("0 0.2 0.2 0.1 0.1\n", encoding="utf-8")

    report = DatasetValidator(dataset_root=dataset_root).validate(write_outputs=False)

    assert report.sequence_count == 1
    assert report.image_count == 2
    assert report.label_count == 2
    assert report.matched_pairs == 1
    assert report.missing_images == 1
    assert report.missing_labels == 1
    assert report.sequences[0].modality == "rgb"
