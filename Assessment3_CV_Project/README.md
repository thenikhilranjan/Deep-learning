# Assessment 3 Search and Rescue Vision

This project implements the Assignment 3 computer vision system for drone-assisted wilderness search and rescue using WiSARD data. The current build includes dataset validation, preprocessing utilities, YOLO dataset preparation, a Streamlit dashboard, SQLite-backed run history, and a classical thermal fallback detector for quick demos before trained weights are available.

## Project Layout

- `app.py`: Streamlit dashboard entrypoint
- `sar_vision/`: core package for data validation, preprocessing, training prep, inference, storage, and UI helpers
- `datasets/`: raw WiSARD dataset files
- `artifacts/`: generated manifests, database, exports, uploads, and model outputs
- `docs/`: planning notes and setup references moved out of the main root
- `notebooks/`: archived course lab notebooks

## What The App Does

- scans the local `datasets/` folder and generates a manifest at `artifacts/cache/dataset_manifest.json`
- reports missing image/label pairs and modality breakdown
- previews preprocessing such as thermal normalization, CLAHE, denoising, grayscale conversion, and resizing
- runs inference using either:
  - a classical thermal hotspot detector available immediately
  - a YOLO model if `.pt` weights are added under `artifacts/models/`
- logs dataset reports and inference runs to `artifacts/db/sar_vision.sqlite3`
- prepares YOLO-ready train/val/test workspaces from the validated manifest

## Setup

1. Activate the project virtual environment.

```bash
source ../venv/bin/activate
```

2. Install project dependencies.

```bash
pip install -r requirements.txt
```

## Validate The Dataset

Run the validator whenever the dataset changes:

```bash
python -m sar_vision.data.validator
```

This writes:

- `artifacts/cache/dataset_manifest.json`
- `artifacts/cache/dataset_summary.json`

## Launch The Dashboard

```bash
streamlit run app.py --server.port 8502
```

Main pages:

- `Overview`: dataset totals and current issues
- `Dataset Status`: sequence summaries and YOLO workspace preparation
- `Preprocessing Lab`: compare original and processed images
- `Inference Demo`: run hotspot or YOLO inference and log the result
- `Run History`: inspect saved dataset reports and inference runs

## Prepare A YOLO Workspace

You can create a YOLO dataset split from the dashboard, or from Python:

```python
from sar_vision.training import YoloTrainingManager

manager = YoloTrainingManager()
data_yaml = manager.prepare_dataset(modality="thermal")
print(data_yaml)
```

This produces a YOLO-ready folder under `artifacts/cache/yolo_dataset/<modality>/`.

## Notes On Training

- The current labels are already in YOLO format.
- `paired` fusion training is intentionally not exported as a standard YOLO dataset yet.
- If you want to train with Ultralytics, place the dataset locally and install `ultralytics` from `requirements.txt`.
- If no model weights are available, the app still works using the classical thermal hotspot detector.

## Run Tests

```bash
pytest tests -q
```

## Current Local Dataset Snapshot

The validator currently detects a large local WiSARD dataset and writes the latest summary into `artifacts/cache/dataset_summary.json`. That summary is the source of truth for what is currently available on disk.
