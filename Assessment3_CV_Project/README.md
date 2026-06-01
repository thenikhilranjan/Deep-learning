# Assessment 3 Search and Rescue Vision

Computer vision coursework project for drone-assisted wilderness search and rescue using **WiSARD** data. The repo combines a Python package (`sar_vision`) for dataset validation, preprocessing, YOLO dataset export, and inference, with a focused Streamlit app (`app.py`, **RescueVision**) for running RGB-only, Thermal-only, or **late-fusion** person detection on uploaded **images, ZIPs of images, or videos**.

Long-form documentation: [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

## Project layout

- `app.py` — RescueVision Streamlit UI (RGB / Thermal / Multimodal late fusion, inference, downloads)
- `sar_vision/` — core library (validator, manifest, preprocessing, YOLO prep, inference service, **late-fusion runner**, storage, UI helpers)
- `sar_vision/inference/fusion.py` — `LateFusionRunner` used by the Multimodal page
- `datasets/` — local WiSARD root (large; see `datasets/README.md`; corpus is gitignored except that README)
- `artifacts/` — generated manifests, optional DB/exports/uploads, **`artifacts/models/`** for `.pt` weights (e.g. `rgb_best_26s.pt`, `Thermal_yolo26m.pt`)
- `tests/` — `pytest` smoke tests
- `docs/` — planning and setup notes

## Setup

```bash
cd /path/to/Assessment3_CV_Project
python3 -m pip install -r requirements.txt
```

If you use a venv at repo parent (e.g. `Cursor/venv`):

```bash
source ../venv/bin/activate
pip install -r requirements.txt
```

## Validate the dataset

```bash
python3 -m sar_vision.data.validator
```

Writes (when not gitignored locally):

- `artifacts/cache/dataset_manifest.json`
- `artifacts/cache/dataset_summary.json`

## Launch the app

```bash
python3 -m streamlit run app.py --server.port 8501
```

Open `http://localhost:8501`. Use **Model Setup** to point at your two checkpoints (RGB `rgb_best_26s.pt` and Thermal `Thermal_yolo26m.pt`), then go to **Inference** and choose one of:

- **RGB only** — upload an RGB image or video.
- **Thermal only** — upload a thermal image or video.
- **Multimodal (Late Fusion)** — upload paired RGB-cropped + thermal inputs (ZIP of images, multiple files, or two videos). The app pairs frames by the numeric id after the final underscore in each filename (e.g. `abc_rgb_000001.jpg` and `xyz_thermal_001.jpg` both match frame 1), resizes RGB to 1250 x 1000 and thermal to 640 x 512, runs both YOLO models, and fuses the predictions by IoU.

## Prepare a YOLO workspace (Python)

```python
from sar_vision.training import YoloTrainingManager

manager = YoloTrainingManager()
data_yaml = manager.prepare_dataset(modality="thermal")
print(data_yaml)
```

Output under `artifacts/cache/yolo_dataset/<modality>/` including `data.yaml`. `paired` multimodal export is not implemented in this manager.

## Run tests

```bash
pytest tests -q
```
