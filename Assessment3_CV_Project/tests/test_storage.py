from pathlib import Path

from sar_vision.storage import DatabaseManager


def test_database_manager_logs_reports_and_runs(tmp_path):
    database = DatabaseManager(db_path=tmp_path / "sar_vision.sqlite3")
    database.initialize()

    report_id = database.log_dataset_report(
        {
            "generated_at": "2026-03-31T00:00:00+00:00",
            "dataset_root": str(tmp_path / "datasets"),
            "sequence_count": 1,
            "image_count": 10,
            "label_count": 9,
            "matched_pairs": 9,
            "missing_images": 0,
            "missing_labels": 1,
            "issues": ["One image has no label"],
        }
    )

    run_id = database.log_run(
        backend="thermal_hotspot",
        model_name="classical_hotspot",
        modality="thermal",
        preprocessing_steps=["thermal_normalization"],
        detections=[
            {
                "label": "person_candidate",
                "confidence": 0.81,
                "x_min": 10,
                "y_min": 12,
                "x_max": 32,
                "y_max": 40,
                "alert_level": "high",
            }
        ],
        input_path="example.png",
        output_path="out.png",
        metrics={"detection_count": 1},
        notes="test run",
    )

    reports = database.fetch_recent_dataset_reports()
    runs = database.fetch_recent_runs()

    assert report_id > 0
    assert run_id > 0
    assert reports[0]["sequence_count"] == 1
    assert runs[0]["backend"] == "thermal_hotspot"
