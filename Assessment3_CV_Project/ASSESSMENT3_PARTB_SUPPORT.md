# Assessment 3 (Part B) - Database Details, GUI Design, Implementation / Development Plan

## Project Title

**Drone-Assisted Wilderness Search and Rescue Using RGB-Thermal Human Detection**

---

## 1. Project Overview

This project focuses on using computer vision to help detect people in wilderness search-and-rescue scenarios from drone imagery. The system is designed to work with aerial **RGB** and **thermal** data so that human targets can still be detected in visually difficult conditions such as poor lighting, cluttered backgrounds, and partial occlusion by trees or terrain.

The project is not only about training a model. It also includes:

- dataset validation
- image preprocessing
- YOLO training preparation
- inference and result visualization
- a GUI for users/operators
- SQLite-based logging of runs and outputs

The long-term research goal is to compare:

- RGB-only detection
- thermal-only detection
- RGB + thermal fusion

---

## 2. Dataset Details

### 2.1 Main Dataset

The main dataset selected for this project is **WiSARD**.

**Public dataset link:**  
[https://sites.google.com/uw.edu/wisard/](https://sites.google.com/uw.edu/wisard/)

This dataset is suitable because it is designed for wilderness search-and-rescue style problems and includes aerial visible and thermal imagery.

### 2.2 Backup Dataset

A backup dataset is **SeaDronesSee**, which can be used if extra comparison data is needed or if WiSARD pairing becomes difficult.

**Public dataset link:**  
[https://seadronessee.cs.uni-tuebingen.de/dataset](https://seadronessee.cs.uni-tuebingen.de/dataset)

### 2.3 Task Type

The task type for this project is:

- **Object Detection**

The aim is to detect human targets and draw bounding boxes around them.

### 2.4 Local Dataset Status in This Project

The project includes a dataset validator that scanned the current local copy of the dataset and produced the following summary:

- Dataset root: `datasets/`
- Total sequence folders detected: `80`
- RGB sequences detected: `39`
- Thermal sequences detected: `41`
- Total images detected: `56,130`
- Total label files detected: `44,664`
- Matched image-label pairs: `44,588`
- Labels without matching image: `76`
- Images without labels: `11,542`

### 2.5 Annotation Format

The current labels are already in **YOLO object detection format**.

Each label file uses the structure:

```text
class_id x_center y_center width height
```

This makes the dataset practical for YOLO-based training preparation.

### 2.6 Dataset Development / Preparation Work

The dataset handling workflow in this project currently does the following:

- scans the dataset folder
- identifies sequence folders
- detects image files and label files
- matches labels and images using the file stem
- infers whether a sequence is RGB or thermal
- writes a dataset manifest and dataset summary

Generated files:

- `artifacts/cache/dataset_manifest.json`
- `artifacts/cache/dataset_summary.json`

### 2.7 Dataset Split Details

The project uses a **sequence-level split strategy** to reduce data leakage. This is important because frames from the same sequence are highly related, so splitting randomly by frame would give unrealistic results.

Planned split ratio:

- **Train:** 70%
- **Validation:** 15%
- **Test:** 15%

Expected split counts from the current local sequence totals:

#### Overall Sequence Split

- Train: `56` sequences
- Validation: `12` sequences
- Test: `12` sequences

#### RGB Sequence Split

- Train: `27` sequences
- Validation: `6` sequences
- Test: `6` sequences

#### Thermal Sequence Split

- Train: `28` sequences
- Validation: `6` sequences
- Test: `7` sequences

### 2.8 Current Dataset Notes

The current validator still reports two important points:

- No explicit paired RGB-thermal sequences have been confirmed by naming rules yet
- `76` labels do not currently have matching local image files in the same folder

This means:

- RGB and thermal single-modality work can already proceed
- fusion work needs more careful pairing confirmation later

---

## 3. Database Details

### 3.1 Database Type

The project uses **SQLite** as the local database.

### 3.2 Why SQLite Was Chosen

SQLite is a good choice for this assignment because:

- it is lightweight
- it does not require a separate database server
- it is easy to use with Python
- it is enough for local project logging and result management

### 3.3 What Is Stored

The database is used to store:

- dataset validation reports
- inference run history
- detection results
- model run metadata
- export/output references

### 3.4 Current Database Tables

The current project includes the following tables:

- `dataset_reports`
- `media_files`
- `model_runs`
- `detections`

### 3.5 What Each Table Is Used For

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
- validation issues

#### `media_files`

Designed to store:

- file path
- dataset name
- modality
- split
- image width and height
- paired media reference if needed later

#### `model_runs`

Stores:

- run time
- backend used
- model name
- modality
- preprocessing steps
- input path
- output path
- metric information
- notes

#### `detections`

Stores:

- predicted label
- confidence
- bounding box coordinates
- alert level

### 3.6 Database File Location

The SQLite database file is stored at:

```text
artifacts/db/sar_vision.sqlite3
```

---

## 4. GUI Design

### 4.1 Type of GUI Planned

The GUI is a:

- **Web Application**

The project uses **Streamlit** to build the interface.

### 4.2 Why a Web App Was Chosen

A web app was chosen because:

- it is easy to run locally
- it is quick to prototype
- it works well with Python and computer vision libraries
- it is good for demonstrations and presentations
- users do not need a separate desktop installation

### 4.3 GUI Style and Theme

The current GUI uses a rescue-style dark theme with:

- dark navy background
- orange and coral action colors
- teal highlights
- metric cards
- charts
- styled information panels

This makes the GUI more eye-catching and easier to present during assessment or demo sessions.

### 4.4 Main GUI Screens

The current GUI is designed around five main pages:

#### 1. Overview

Shows:

- dataset totals
- modality coverage
- current validation issues
- assignment alignment summary

#### 2. Dataset Status

Shows:

- sequence-level dataset breakdown
- modality filters
- dataset health state filters
- dataset refresh option
- YOLO workspace preparation tools

#### 3. Preprocessing Lab

Shows:

- original image
- processed image
- preprocessing settings
- intensity profile / histogram view
- processed image export option

#### 4. Inference Demo

Shows:

- dataset image, sample image, or uploaded image
- modality selection
- inference backend selection
- threshold controls
- annotated detection output
- detections table
- export buttons

#### 5. Run History

Shows:

- dataset report history
- inference history
- backend usage summary
- CSV export options

### 4.5 Low-Fidelity GUI Wireframes

Below are simple text wireframes that show how the GUI is planned/presented.

#### Wireframe 1 - Overview Page

```text
+----------------------------------------------------------------------------------+
| Search and Rescue Vision Dashboard                                               |
+----------------------------------------------------------------------------------+
| Hero Banner: Project intro, mission summary, status                              |
+----------------------------------------------------------------------------------+
| Sequences | Images | Labels | Matched Pairs                                      |
+----------------------------------------------------------------------------------+
| Assignment Alignment Panel     | Modality Coverage Chart                         |
| - Dataset validation           | RGB / Thermal comparison                        |
| - Preprocessing                |                                                |
| - Training prep                |                                                |
| - Inference + Logging          |                                                |
+----------------------------------------------------------------------------------+
| Current Dataset Issues                                                          |
| - Missing images / labels                                                       |
| - Pairing not yet fully confirmed                                               |
+----------------------------------------------------------------------------------+
```

#### Wireframe 2 - Inference Demo Page

```text
+----------------------------------------------------------------------------------+
| Inference Demo                                                                   |
+----------------------------------------------------------------------------------+
| Image Source | Modality | Backend | Threshold | Preprocessing Controls           |
+----------------------------------------------------------------------------------+
| Original / Selected Image         | Annotated Detection Output                   |
|                                   | Bounding boxes + confidence                  |
|                                   | Export annotated image                       |
+----------------------------------------------------------------------------------+
| Detection Table                                                                  |
| Label | Confidence | Coordinates | Alert Level                                  |
+----------------------------------------------------------------------------------+
| Download CSV | Run History Update | Saved Output Path                            |
+----------------------------------------------------------------------------------+
```

### 4.6 Note About Screenshots

If actual screenshots are needed for submission, they can be taken directly from the running app after launching:

```bash
streamlit run app.py --server.port 8502
```

Then open:

```text
http://localhost:8502
```

---

## 5. Implementation / Development Plan

### 5.1 Core Technologies Used

The project is built using:

- Python
- Streamlit
- OpenCV
- NumPy
- Pandas
- Pillow
- Altair
- SQLite
- Ultralytics YOLO
- Pytest

### 5.2 CNN / Detection Architectures Planned to Explore

The planned model exploration is:

#### 1. Thermal Baseline

- **YOLOv8n**
- used as the first lightweight object detection baseline
- suitable for quick experimentation and lower compute use

#### 2. RGB Baseline

- **YOLOv8n**
- same architecture used for RGB-only comparison

#### 3. Stronger Follow-Up Model

- **YOLOv8s** or another slightly larger YOLO variant
- only if time and compute allow

#### 4. Fusion Stage

- RGB + thermal **late fusion** or other simple paired strategy
- this will be added after RGB and thermal baselines are working

#### 5. Classical Non-Deep-Learning Baseline

- thermal hotspot detector
- useful for quick GUI demos before trained weights are available

### 5.3 Training Strategy

The planned training strategy is:

- use **transfer learning** from pretrained YOLO weights such as `yolov8n.pt`
- start with the lightweight model first
- use YOLO-format training data generated from the local manifest
- use sequence-level train/validation/test split
- train at image size `640`
- start with around `20` epochs for the first baseline
- use Ultralytics default training setup first, then tune if needed

### 5.4 Optimizer / Training Configuration Plan

The first training stage will use the default optimizer and training flow from **Ultralytics YOLO** because it is stable and easy to reproduce.

If tuning is needed later, possible changes include:

- adjusting learning rate
- changing optimizer selection
- increasing or decreasing epochs
- moving from `yolov8n` to a larger variant

### 5.5 Testing Plan

The testing plan includes:

- validating the dataset before training
- creating proper train/validation/test splits
- testing on unseen sequences
- checking model behavior on both RGB and thermal images
- testing the GUI using dataset images, sample images, and uploaded images
- exporting results for manual review

### 5.6 Accuracy / Evaluation Plan

The main metrics planned for evaluation are:

- precision
- recall
- F1-score
- mAP

For this search-and-rescue task, **recall is very important**, because missing a person is more serious than having a few extra false positives.

### 5.7 Current Accuracy Status

At the moment:

- the YOLO training pipeline is prepared
- the dataset validator is working
- the GUI is working
- but **final trained YOLO weights are not yet included**

So:

- **actual final model accuracy is not known yet**
- the real accuracy will be measured after training the thermal and RGB baselines

### 5.8 Error Handling Plan

The project includes both technical and model-related error handling.

#### Dataset-Level Error Handling

- detect missing images
- detect missing labels
- report mismatched image-label pairs
- generate validation summary before training

#### Model-Level Error Handling

To reduce **overfitting**, the plan is:

- use proper train/validation/test split by sequence
- monitor validation performance
- use transfer learning instead of training from scratch
- start with smaller models first
- use data augmentation through YOLO training pipeline

To reduce **underfitting**, the plan is:

- increase epochs if needed
- improve preprocessing
- test larger model variants if compute allows
- tune image size and training settings

To handle **data quality issues**, the plan is:

- re-run dataset validation after any changes
- inspect problematic sequences manually
- use GUI previews to confirm image quality and preprocessing behavior

### 5.9 Tentative Timeline

#### Phase 1 - Dataset and Setup

- clean project structure
- validate dataset
- generate manifest and summary
- set up database and GUI skeleton

#### Phase 2 - Preprocessing and Training Prep

- implement thermal normalization
- add contrast enhancement and denoising
- prepare YOLO split generation

#### Phase 3 - Thermal Baseline

- train the first thermal YOLO model
- evaluate precision, recall, F1, and mAP

#### Phase 4 - RGB Baseline

- train the RGB YOLO model
- compare with the thermal baseline

#### Phase 5 - Fusion Improvement

- confirm RGB-thermal pairing
- implement a simple late-fusion pipeline

#### Phase 6 - Demo and Final Reporting

- run inference in GUI
- export sample results
- create final performance summary
- prepare presentation/demo material

---

## 6. Deployment Plan

### 6.1 Recommended Deployment Style

The best deployment method for this project is:

- **Local deployment**

This is recommended because:

- the dataset is large
- the project works best when it can access local files directly
- model files can also be large
- Streamlit works well for local demos and presentations

### 6.2 Deployment Steps

#### Step 1

Open the project folder:

```bash
cd /Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project
```

#### Step 2

Activate the virtual environment:

```bash
source ../venv/bin/activate
```

#### Step 3

Install dependencies:

```bash
pip install -r requirements.txt
```

#### Step 4

Validate the dataset:

```bash
python -m sar_vision.data.validator
```

#### Step 5

Launch the GUI:

```bash
streamlit run app.py --server.port 8502
```

#### Step 6

Open the GUI in a browser:

```text
http://localhost:8502
```

### 6.3 Optional Training Step

To prepare YOLO training data:

```python
from sar_vision.training import YoloTrainingManager

manager = YoloTrainingManager()
data_yaml = manager.prepare_dataset(modality="thermal")
print(data_yaml)
```

---

## 7. Current Project Status

The following parts are already working:

- dataset validation
- dataset manifest generation
- preprocessing tools
- YOLO workspace preparation
- SQLite logging
- Streamlit GUI
- image and CSV export
- smoke tests

### Current Test Status

The project has already been checked with:

- Python compile checks
- smoke tests using `pytest`
- live Streamlit startup checks
- browser-based GUI walkthroughs

### Honest Current Limitation

The main limitation at this stage is:

- final YOLO model training and final accuracy reporting are still pending

So the project is already a strong working framework, but final benchmark numbers will come after full training.

---

## 8. Conclusion

This project is a well-structured Assignment 3 implementation for a drone-based search-and-rescue vision system. It already includes the important building blocks:

- dataset handling
- preprocessing
- database support
- GUI design
- training preparation
- inference workflow

It is practical, easy to demonstrate, and ready to be extended into full model training and evaluation.
