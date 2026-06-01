# Assessment 3 Project Guide

## 1. Introduction

This file explains the full Assignment 3 project in a simple and practical way.

The project is about **drone-assisted wilderness search and rescue**. The idea is to use computer vision to help detect people from aerial images. The long-term goal is to compare:

- RGB-only detection
- thermal-only detection
- RGB + thermal fusion

To support that goal, the project includes:

- dataset validation
- preprocessing tools
- YOLO training preparation
- an inference pipeline (in the `sar_vision` package)
- a Streamlit GUI entry point (`app.py`)
- SQLite logging for results and history (used when you run inference through `sar_vision` APIs or older dashboard-style flows)

**How the repo is organized today**

- **`sar_vision/`** holds the main engineering code: manifest generation, preprocessing, YOLO dataset export, optional classical/YOLO `DetectionService`, SQLite `DatabaseManager`, and tests.
- **`app.py`** is the operator-facing **RescueVision** app: a focused interface that loads two Ultralytics YOLO weights (RGB and Thermal), lets the user pick one of three **Approaches** — *RGB only*, *Thermal only*, or *Multimodal (Late Fusion)* — and runs inference on uploaded **images, ZIPs of images, or videos**. The multimodal mode does not use a third checkpoint; it runs the RGB and Thermal models in parallel and fuses their predictions via the `LateFusionRunner` in [`sar_vision/inference/fusion.py`](sar_vision/inference/fusion.py).

This guide is written so that someone new to the project can understand:

- what the project is
- what dataset is being used
- what technology was used
- how the project was built
- how the GUI works
- how to run or deploy the project
- what is finished already and what can be extended later

---

## 2. Project Goal

The main goal of this project is to build a **search and rescue vision system** that can help identify human targets in difficult outdoor environments.

This problem is important because:

- rescue missions are time-sensitive
- people may be small and hard to see in aerial images
- trees, shadows, rocks, and background clutter make detection difficult
- thermal images can help in low-light or visually confusing situations

The system was designed not just as a model experiment, but as a **complete mini-project** with:

- data handling
- preprocessing
- model preparation
- inference
- experiment logging
- a usable GUI

---

## 3. Project Idea in Simple Words

In simple terms, the system works like this:

1. We place the dataset inside the project.
2. The project scans the dataset and checks what is available.
3. It builds a structured manifest of images, labels, and sequence details.
4. It allows us to preview image preprocessing such as contrast enhancement and thermal normalization.
5. It can prepare the dataset in YOLO format for training.
6. The Streamlit app can run **YOLO-based** person detection on uploaded image or video using your saved `.pt` weights.
7. When you use the `sar_vision` inference + storage path, reports and inference history can be stored in SQLite.

So this is not only a notebook or only a report. It is a **working project structure** that can be used for experimentation and demonstration.

---

## 4. Problem Statement

The project focuses on the problem of finding people in wilderness scenes from drone imagery.

This is difficult because:

- human targets may occupy only a very small part of the image
- the background can be highly cluttered
- lighting conditions may be poor
- thermal and RGB data may not always be perfectly aligned

Because of these difficulties, the project combines:

- **computer vision**
- **image preprocessing**
- **deep learning preparation**
- **GUI-based visualization**

---

## 5. Dataset Details

### Main Dataset

The main dataset used in this project is **WiSARD**.

WiSARD is suitable because it is designed for search-and-rescue style scenes and contains both visible and thermal aerial data.

### Local Dataset Status in This Project

The project includes a validator that scans the local dataset folder and produces a summary.

Current local validation summary:

- dataset root: `datasets/`
- total sequence folders detected: `80`
- RGB sequences detected: `39`
- thermal sequences detected: `41`
- total images detected: `56,130`
- total label files detected: `44,664`
- matched image-label pairs: `44,588`
- labels without matching local image: `76`
- images without labels: `11,542`

### Current Observations

The validator currently reports:

- no paired RGB-thermal sequences were detected from local naming rules
- some labels do not have matching images in the same folder

This does **not** mean the dataset is unusable. It means:

- the local copy is large and mostly usable
- RGB and thermal single-modality work is already possible
- explicit fusion pairing still needs to be confirmed more carefully

### Annotation Format

The local labels are already in **YOLO format**.

That means each label file contains values like:

```text
class_id x_center y_center width height
```

These values are normalized, so they are ready for YOLO-style training preparation.

### Why Dataset Validation Was Important

Before building the training and GUI workflow, we needed to confirm:

- which sequence folders exist
- which images and labels are available
- whether RGB and thermal data are both present
- how many files match correctly
- what problems exist in the local copy

That is why dataset validation was implemented as one of the first major project steps.

---

## 6. How We Built the Project

The project was built in stages so it would be clean, maintainable, and easy to extend.

### Step 1: Clean Up the Project Folder

The root folder originally contained:

- planning notes
- setup notes
- notebooks
- assignment files
- project code in progress

We reorganized it to make the project easier to manage.

Now the folder is cleaner and structured into:

- `sar_vision/` for source code
- `datasets/` for data (large WiSARD tree is local-only; see `datasets/README.md`)
- `artifacts/` for outputs and generated files (including `artifacts/models/` for `.pt` weights such as `rgb_best_26s.pt` and `Thermal_yolo26m.pt`)
- `tests/` for smoke tests
- `docs/` for planning and setup notes
- `.streamlit/` for Streamlit theme/config

Course **Part B** written deliverables (support markdown, `.txt`, `.docx`) were moved **outside** this folder to the parent directory next to `Assessment3_CV_Project` so the code project stays easy to navigate.

### Step 2: Add Dataset Validation

We created a validator that:

- scans the dataset tree
- finds images and labels
- matches them by stem name
- infers modality from folder names
- counts images, labels, matched pairs, and issues
- writes outputs to:
  - `artifacts/cache/dataset_manifest.json`
  - `artifacts/cache/dataset_summary.json`

This makes the data status visible to both developers and the GUI.

### Step 3: Build the Core Python Package

We created a proper Python package named `sar_vision`.

It contains separate modules for:

- config
- dataset handling
- preprocessing
- training prep
- inference
- storage
- UI helpers

This makes the project easier to scale and easier to understand than putting everything inside one notebook or one script.

### Step 4: Add Preprocessing Tools

The project supports preprocessing operations such as:

- thermal normalization
- CLAHE contrast enhancement
- denoising
- grayscale conversion
- resizing
- image tiling helpers

These operations are useful for:

- improving image visibility
- exploring preprocessing effects
- preparing data for training or inference

### Step 5: Add Training Preparation

A YOLO training manager was added to prepare the dataset for training.

This part of the system:

- reads the dataset manifest
- filters by modality
- creates train/val/test splits by sequence
- creates YOLO folder structure
- generates a `data.yaml` file

It supports:

- thermal-only preparation
- RGB-only preparation
- all-modality preparation

The project does **not** yet export paired fusion training as a normal YOLO dataset, because fusion needs a separate paired-data design.

### Step 6: Add Inference Logic

The inference layer supports two paths:

1. **Classical thermal hotspot detection**
   - works immediately
   - useful for demos and quick testing
   - does not require trained YOLO weights

2. **YOLO-based inference**
   - works when `.pt` weights are available
   - intended for actual trained model experiments

This dual approach is useful because it gives the GUI something practical to show even before final model training is complete.

### Step 7: Add SQLite Logging

To support project traceability and GUI history, SQLite was added.

The implemented database stores:

- dataset validation reports
- inference runs
- detections
- metadata for outputs

This matches the assignment idea of having database details, but keeps it lightweight and suitable for a student project.

### Step 8: Build the GUI

The project GUI is **Streamlit**, implemented in [`app.py`](app.py) as **RescueVision**:

- **Home**: short mission summary and three approach cards (RGB, Thermal, Multimodal late fusion).
- **Model Setup**: edit and verify paths to the two YOLO checkpoints (defaults: `artifacts/models/rgb_best_26s.pt`, `artifacts/models/Thermal_yolo26m.pt`). Late fusion uses these two models together; there is no third file.
- **Inference**: pick an **Approach** (RGB only / Thermal only / Multimodal Late Fusion).
  - *RGB only / Thermal only*: upload **image or video**, set confidence and max frames, run detection.
  - *Multimodal (Late Fusion)*: upload paired RGB-cropped and thermal inputs as a **ZIP** of images, **multiple image files**, or **two videos**. Frames are matched by the numeric id after the final `_` in the filename. RGB is resized to 1250 x 1000, thermal to 640 x 512, and fused detections are returned along with annotated thermal/RGB frames and YOLO label files, packaged into a downloadable ZIP.
- **About**: one-page explanation for demos and marking.

Styling uses a dark “mission console” layout with custom CSS for readability and spacing.

---

## 7. Technologies Used

### Programming Language

- Python

### Libraries and Frameworks

- `streamlit` for the GUI
- `numpy` for array operations
- `pandas` for tables and summaries (used in `app.py` for detection tables)
- `opencv-python` for image handling, video frame IO, and preprocessing in `sar_vision`
- `Pillow` for safe image metadata loading
- `altair` is listed in dependencies for optional charting; the current `app.py` does not depend on it
- `sqlite3` for local database storage when using `sar_vision.storage`
- `ultralytics` for YOLO training and inference (required for `app.py` and `YoloTrainingManager`)
- `pytest` for smoke testing

### Why These Technologies Were Chosen

- **Python** is widely used for computer vision and rapid prototyping
- **Streamlit** is fast to build and easy to demo
- **OpenCV** is reliable for image preprocessing and display work
- **SQLite** is enough for a local course project and easy to manage
- **Ultralytics YOLO** matches the dataset label format and is practical for baseline training

---

## 8. Folder Structure

Here is the important structure of the project:

```text
Assessment3_CV_Project/
├── app.py                 # RescueVision Streamlit UI (YOLO image/video)
├── README.md
├── PROJECT_GUIDE.md
├── requirements.txt
├── .streamlit/
├── datasets/              # WiSARD root (local); tracked README only in git
├── artifacts/
│   ├── cache/               # manifest, summary, yolo_dataset (generated)
│   ├── db/
│   ├── exports/
│   ├── uploads/
│   └── models/              # e.g. rgb_best_26s.pt, Thermal_yolo26m.pt
├── sar_vision/              # core library (validator, training prep, inference service, DB)
├── tests/
└── docs/
```

### Important Folders Explained

- `datasets/`: raw WiSARD dataset files
- `artifacts/cache/`: dataset manifest and summary files
- `artifacts/db/`: SQLite database
- `artifacts/exports/`: exported annotated images and outputs
- `artifacts/models/`: trained model weights (defaults: `rgb_best_26s.pt`, `Thermal_yolo26m.pt`)
- `sar_vision/`: actual project source code
- `tests/`: smoke tests to verify the core system

---

## 9. GUI Details

The GUI is one of the most important parts of this project because the assignment requires a usable operator-facing interface.

### GUI Theme

RescueVision uses:

- a dark navy/slate background with high-contrast text
- card-style panels and a hero header on Home
- sidebar navigation
- progress feedback for long video runs

### GUI Pages (current `app.py`)

#### 1. Home

- mission-style title and short description
- three cards describing the RGB, Thermal, and Multimodal late-fusion approaches
- numbered workflow for first-time users

#### 2. Model Setup

- two text fields for the RGB and Thermal model file paths
- per-model “found / not found” feedback
- progress bar for how many of the two paths resolve to real files
- caption explaining that the multimodal approach reuses these two models via late fusion

#### 3. Inference

- top-level **Approach** selector: *RGB only*, *Thermal only*, *Multimodal (Late Fusion)*
- *RGB only / Thermal only*: image vs video, confidence, max video frames, file upload; side-by-side preview, detection table, PNG/CSV/MP4 downloads
- *Multimodal (Late Fusion)*: input type *Images* (ZIP or multiple files per modality) or *Videos* (one RGB video + one thermal video); advanced sliders for RGB / Thermal confidence and fusion IoU; results show KPI cards, thermal/RGB galleries, label previews, and a single ZIP download of the fused output folder

#### 4. About

- short bullet summary for presentations and Part B explanation

### Relationship to `sar_vision`

Dataset validation, preprocessing previews, YOLO workspace export, classical hotspot fallback, the late-fusion runner (`LateFusionRunner` in [`sar_vision/inference/fusion.py`](sar_vision/inference/fusion.py)), and SQLite run logging are implemented in **`sar_vision/`** and documented in this guide and [`README.md`](README.md). You can run the validator from the command line and use `YoloTrainingManager`, `DetectionService`, or `LateFusionRunner` from Python or notebooks. The current Streamlit `app.py` is intentionally streamlined for **trained YOLO demo inference** with two single-modality weights plus a late-fusion option.

### GUI Purpose

The GUI demonstrates:

- practical operator workflow (configure models, upload media, run, export)
- multimodal model comparison at the UI level (which weight file you select)
- clear outputs suitable for screenshots in reports

This makes it a strong fit for the assignment requirement.

---

## 10. Database Details

The project uses **SQLite** as a lightweight local database.

### Why SQLite

SQLite was chosen because:

- it is simple
- no server setup is required
- it works well for local development
- it is enough for this assignment

### Implemented Tables

The current code creates these tables:

- `dataset_reports`
- `media_files`
- `model_runs`
- `detections`

### What Is Stored

#### `dataset_reports`

Stores:

- dataset root
- generated time
- sequence count
- image count
- label count
- matched pairs
- missing images
- missing labels
- issues

#### `model_runs`

Stores:

- run time
- backend used
- model name
- modality
- preprocessing steps
- input path
- output path
- metrics
- notes

#### `detections`

Stores:

- label
- confidence
- bounding box coordinates
- alert level

This makes it easy to review what happened during inference and what settings were used.

---

## 11. How to Run the Project

### Step 1: Open the Project Folder

Work inside:

```bash
cd /Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project
```

### Step 2: Activate the Virtual Environment

```bash
source ../venv/bin/activate
```

### Step 3: Install Requirements

```bash
pip install -r requirements.txt
```

### Step 4: Validate the Dataset

```bash
python -m sar_vision.data.validator
```

This creates:

- `artifacts/cache/dataset_manifest.json`
- `artifacts/cache/dataset_summary.json`

### Step 5: Launch the GUI

From the project folder (use your own venv or `python3 -m pip install -r requirements.txt` as needed):

```bash
python3 -m streamlit run app.py --server.port 8501
```

Then open:

```text
http://localhost:8501
```

### Step 6: Run Tests

```bash
pytest tests -q
```

---

## 12. How to Prepare the Dataset for YOLO Training

The project already includes YOLO workspace preparation.

Do this from **Python** (or your own notebook) using `YoloTrainingManager`. The current `app.py` does not include the older multi-page “Dataset Status / YOLO workspace” UI.

### Python Example

```python
from sar_vision.training import YoloTrainingManager

manager = YoloTrainingManager()
data_yaml = manager.prepare_dataset(modality="thermal")
print(data_yaml)
```

This creates a YOLO-ready dataset structure inside:

```text
artifacts/cache/yolo_dataset/thermal/
```

It includes:

- `images/train`
- `images/val`
- `images/test`
- `labels/train`
- `labels/val`
- `labels/test`
- `data.yaml`

### Supported Modes

- `thermal`
- `rgb`
- `all`

### Current Limitation

`paired` fusion is not exported in this same YOLO workflow yet, because that requires special paired alignment logic.

---

## 13. How to Deploy the Project

### Recommended Deployment Method

For this project, the most realistic deployment is **local deployment** on a machine that already has:

- Python installed
- the dataset available locally
- the virtual environment set up

This is recommended because:

- the dataset is large
- image files are stored locally
- model files may also be large
- the dashboard works best when it can access the local dataset directly

### Local Deployment Steps

1. Copy the full project folder.
2. Make sure the dataset is inside `datasets/`.
3. Activate the virtual environment.
4. Install dependencies with `pip install -r requirements.txt`.
5. Run `python -m sar_vision.data.validator`.
6. Launch with `python3 -m streamlit run app.py --server.port 8501` (or another free port).

### Optional Remote Deployment

It is possible to deploy the Streamlit app remotely, but for a real deployment you would need:

- the full dataset mounted or copied to the server
- model weights available on the server
- storage path adjustments if directory structure changes

For coursework and demo purposes, **local deployment is the best option**.

---

## 14. What Is Already Working

The following parts are already working:

- dataset validation
- dataset manifest generation
- modality detection from sequence names
- YOLO-format label parsing
- preprocessing tools
- YOLO dataset workspace generation
- **RescueVision** Streamlit GUI (`app.py`): three-model paths, image/video YOLO inference, downloads
- SQLite logging and classical/YOLO `DetectionService` when using `sar_vision` APIs (not required for the minimal `app.py` path)
- smoke tests for core `sar_vision` modules

### Current Verification Status

The project has already been tested with:

- Python compile checks
- smoke tests using `pytest`
- live Streamlit startup checks
- browser-based GUI walkthroughs

Run `pytest tests -q` after dependency and dataset path changes to confirm everything still passes.

---

## 15. What Is Not Fully Finished Yet

To be honest and accurate, these parts are still future or partial work:

- final trained YOLO model weights are not bundled by default
- RGB-thermal fusion pairing is not fully implemented yet
- paired-fusion training is not yet exported in the same way as single-modality YOLO prep
- full benchmark result tables still depend on training experiments

This means the project is already a strong working framework, but the final research comparison still depends on additional model training and fusion work.

---

## 16. Why This Project Is Strong for the Assignment

This project fits the assignment well because it includes all the important parts:

- a real rescue-related computer vision problem
- a large real dataset
- preprocessing and dataset analysis
- training preparation
- inference workflow
- database logging
- a polished and usable GUI
- clear project structure

It is not just a report and not just a notebook. It is a proper project that can be extended into a final presentation and model comparison study.

---

## 17. Suggested Next Steps

The best next steps are:

1. train the first thermal YOLO baseline
2. train the first RGB YOLO baseline
3. save `.pt` weights into `artifacts/models/`
4. compare the results inside the GUI
5. later add explicit RGB-thermal pairing and fusion logic

---

## 18. Final Summary

This project is a **search and rescue computer vision system** built around the WiSARD dataset. It includes:

- dataset validation
- preprocessing
- YOLO training preparation
- inference (library + optional classical fallback)
- SQLite-based logging when using the storage layer
- a Streamlit **RescueVision** GUI for demonstrating three YOLO checkpoints on image and video

The project is already understandable, runnable, and demonstrable. It also has a clear path for future improvement, especially for trained model baselines and RGB-thermal fusion experiments.
