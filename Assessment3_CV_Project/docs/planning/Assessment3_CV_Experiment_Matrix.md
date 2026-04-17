# Assessment 3 Experiment Matrix

This file is for project planning only.
Do not submit it as-is. Convert it into your own notes, slides, and report content.

## Goal

Keep the experimental plan focused, defendable, and realistic for a 3-person team.

## Core Research Question

Does RGB-thermal fusion improve drone-based person detection for search and rescue compared with single-modality baselines?

## Minimum Viable Experiment Set

| ID | Setup | Input | Main Question | Recommended Output |
| --- | --- | --- | --- | --- |
| E1 | RGB baseline | RGB images only | How well does a standard detector work on visible imagery? | Precision, recall, F1, mAP, sample detections |
| E2 | Thermal baseline | Thermal images only | Is thermal more reliable under poor visibility or clutter? | Precision, recall, F1, mAP, sample detections |
| E3 | Fusion model | Paired RGB + thermal | Does fusion improve recall and robustness? | Same metrics plus side-by-side qualitative results |
| E4 | Preprocessing ablation | Best modality from E1-E3 | Does image processing improve performance? | Before/after metric table |

## Suggested Models

Keep the final set small. A good version is:
- one `YOLO` family detector as the main baseline
- one `RT-DETR` style model for a stronger comparison
- one simple fusion method for paired RGB-thermal data

If training time becomes a problem:
- keep one detector family only
- compare modality and preprocessing instead of too many architectures

## Preprocessing Ablations

Use only a few meaningful image-processing experiments.

### RGB
- CLAHE or contrast enhancement
- gamma correction for dark frames
- denoising if noise is visible

### Thermal
- intensity normalization
- denoising
- histogram equalization or contrast enhancement

### Small-Object Handling
- image tiling
- centered crops
- resizing strategy comparison

## What To Measure

### Quantitative Metrics
- precision
- recall
- F1-score
- mAP

### Qualitative Analysis
- missed detections under tree cover
- false positives on rocks, branches, or background clutter
- performance differences between RGB and thermal views

## Recommended Success Story

Your best storyline is not "our model got the highest number."

Your best storyline is:
- RGB works well in clearer daylight scenes
- thermal helps when visibility is poor or the target blends into the background
- fusion gives the most reliable overall rescue-oriented performance

That is easier to defend academically than chasing one headline metric.

## Dataset Strategy

### Primary Path
- use `WiSARD` as the main dataset for wilderness search and rescue

### Backup Path
- use `SeaDronesSee` if annotation preparation, pairing, or download constraints slow down WiSARD experiments

### Practical Rule
- finish a complete baseline pipeline on one dataset before expanding scope

## Demo Storyboard

### Guaranteed Demo

1. Open the GUI with a prerecorded UAV image or clip.
2. Run the RGB-only model.
3. Show missed or weak detections.
4. Run the thermal-only or fusion model on the same scene.
5. Compare boxes, confidence, and operator-facing summary.
6. End with one failure case and explain future improvements.

### What To Prepare Before Demo Day

- 2 to 3 short clips or image sets that always work
- one strong success example
- one challenging example with occlusion or poor lighting
- screenshots of the GUI in case live inference is slow
- a backup recorded screen-capture of the full demo flow

## Optional Hardware Bonus

If hardware becomes available later, keep the extra demo simple:
- read a live camera or drone stream into the GUI
- run whichever trained model is most stable
- present it as a bonus proof-of-concept only

Do not make your project depend on:
- live autonomous flight
- custom drone data collection
- onboard inference claims you cannot test properly

## Team Split Suggestion

### Member 1
- dataset preparation
- annotation conversion
- preprocessing pipeline

### Member 2
- baseline model training
- evaluation and result tables

### Member 3
- GUI and demo integration
- visualizations and presentation assets

All members should still understand the full pipeline for oral defense.

## Scope Guardrails

Cut scope if needed in this order:
1. reduce number of architectures
2. reduce number of preprocessing variants
3. reduce GUI features

Do not cut:
1. baseline comparison
2. evaluation discussion
3. clear demo flow
