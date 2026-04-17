"""SQLite persistence for dataset reports and inference runs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sar_vision.config import get_settings


class DatabaseManager:
    """Lightweight SQLite storage aligned with the project report."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.settings.ensure_runtime_dirs()
        self.db_path = db_path or self.settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Create all required tables if they do not exist."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS dataset_reports (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generated_at TEXT NOT NULL,
                    dataset_root TEXT NOT NULL,
                    sequence_count INTEGER NOT NULL,
                    image_count INTEGER NOT NULL,
                    label_count INTEGER NOT NULL,
                    matched_pairs INTEGER NOT NULL,
                    missing_images INTEGER NOT NULL,
                    missing_labels INTEGER NOT NULL,
                    issues_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS media_files (
                    media_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    dataset_name TEXT,
                    modality TEXT,
                    split TEXT,
                    width INTEGER,
                    height INTEGER,
                    paired_media_id INTEGER
                );

                CREATE TABLE IF NOT EXISTS model_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    preprocessing_json TEXT NOT NULL,
                    input_path TEXT,
                    output_path TEXT,
                    metric_json TEXT NOT NULL,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS detections (
                    detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    predicted_label TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    x_min INTEGER NOT NULL,
                    y_min INTEGER NOT NULL,
                    x_max INTEGER NOT NULL,
                    y_max INTEGER NOT NULL,
                    alert_level TEXT,
                    FOREIGN KEY(run_id) REFERENCES model_runs(run_id)
                );
                """
            )
            connection.commit()

    def log_dataset_report(self, report: Dict[str, Any]) -> int:
        """Persist a compact dataset validation summary."""
        self.initialize()
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO dataset_reports (
                    generated_at,
                    dataset_root,
                    sequence_count,
                    image_count,
                    label_count,
                    matched_pairs,
                    missing_images,
                    missing_labels,
                    issues_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report["generated_at"],
                    report["dataset_root"],
                    report["sequence_count"],
                    report["image_count"],
                    report["label_count"],
                    report["matched_pairs"],
                    report["missing_images"],
                    report["missing_labels"],
                    json.dumps(report.get("issues", [])),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def log_run(
        self,
        *,
        backend: str,
        model_name: str,
        modality: str,
        preprocessing_steps: Iterable[str],
        detections: Iterable[Dict[str, Any]],
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Store an inference run and its detections."""
        self.initialize()
        metrics = metrics or {}
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO model_runs (
                    created_at,
                    backend,
                    model_name,
                    modality,
                    preprocessing_json,
                    input_path,
                    output_path,
                    metric_json,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    backend,
                    model_name,
                    modality,
                    json.dumps(list(preprocessing_steps)),
                    input_path,
                    output_path,
                    json.dumps(metrics),
                    notes,
                ),
            )
            run_id = int(cursor.lastrowid)

            for detection in detections:
                cursor.execute(
                    """
                    INSERT INTO detections (
                        run_id,
                        predicted_label,
                        confidence_score,
                        x_min,
                        y_min,
                        x_max,
                        y_max,
                        alert_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        detection["label"],
                        detection["confidence"],
                        detection["x_min"],
                        detection["y_min"],
                        detection["x_max"],
                        detection["y_max"],
                        detection.get("alert_level"),
                    ),
                )

            connection.commit()
            return run_id

    def fetch_recent_runs(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Return recent inference runs for the dashboard."""
        self.initialize()
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    run_id,
                    created_at,
                    backend,
                    model_name,
                    modality,
                    preprocessing_json,
                    input_path,
                    output_path,
                    metric_json,
                    notes
                FROM model_runs
                ORDER BY run_id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["preprocessing_json"] = json.loads(payload["preprocessing_json"])
            payload["metric_json"] = json.loads(payload["metric_json"])
            results.append(payload)
        return results

    def fetch_recent_dataset_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent dataset summaries for the dashboard."""
        self.initialize()
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    report_id,
                    generated_at,
                    dataset_root,
                    sequence_count,
                    image_count,
                    label_count,
                    matched_pairs,
                    missing_images,
                    missing_labels,
                    issues_json
                FROM dataset_reports
                ORDER BY report_id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["issues_json"] = json.loads(payload["issues_json"])
            results.append(payload)
        return results
