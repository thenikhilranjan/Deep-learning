"""Shared project configuration and paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
LABEL_EXTENSIONS = {".txt"}


@dataclass(frozen=True)
class Settings:
    """Centralized paths and defaults for the project."""

    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    default_class_names: Tuple[str, ...] = ("person",)
    default_image_size: int = 640

    datasets_dir: Path = field(init=False)
    artifacts_dir: Path = field(init=False)
    cache_dir: Path = field(init=False)
    exports_dir: Path = field(init=False)
    uploads_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    dataset_manifest_path: Path = field(init=False)
    dataset_summary_path: Path = field(init=False)

    def __post_init__(self) -> None:
        artifacts_dir = self.project_root / "artifacts"
        cache_dir = artifacts_dir / "cache"
        models_dir = artifacts_dir / "models"
        db_dir = artifacts_dir / "db"

        object.__setattr__(self, "datasets_dir", self.project_root / "datasets")
        object.__setattr__(self, "artifacts_dir", artifacts_dir)
        object.__setattr__(self, "cache_dir", cache_dir)
        object.__setattr__(self, "exports_dir", artifacts_dir / "exports")
        object.__setattr__(self, "uploads_dir", artifacts_dir / "uploads")
        object.__setattr__(self, "models_dir", models_dir)
        object.__setattr__(self, "db_dir", db_dir)
        object.__setattr__(self, "db_path", db_dir / "sar_vision.sqlite3")
        object.__setattr__(
            self, "dataset_manifest_path", cache_dir / "dataset_manifest.json"
        )
        object.__setattr__(
            self, "dataset_summary_path", cache_dir / "dataset_summary.json"
        )

    def ensure_runtime_dirs(self) -> None:
        """Create runtime directories that the app relies on."""
        for path in (
            self.datasets_dir,
            self.artifacts_dir,
            self.cache_dir,
            self.exports_dir,
            self.uploads_dir,
            self.models_dir,
            self.db_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


_SETTINGS = Settings()


def get_settings() -> Settings:
    """Return the singleton settings object for the project."""
    return _SETTINGS
