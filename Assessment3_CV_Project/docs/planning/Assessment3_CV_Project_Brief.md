# Assessment 3 CV Project Brief

This document is for planning, consultation, and team discussion.
Do not submit it verbatim. Rewrite all academic content in your own words so your submission stays aligned with the subject's GenAI rules.

## Recommended Direction

**Main idea:** Drone-assisted wilderness search and rescue using RGB and thermal human detection.

**Why this is the strongest option**
- It is less common than road crack, pothole, or generic traffic detection projects.
- It has clear social impact and a strong real-world story.
- It naturally combines computer vision, image processing, deep learning, and GUI design.
- It gives your team a good comparison study: RGB-only vs thermal-only vs multimodal fusion.
- It works with public datasets first, so the project does not depend on borrowing hardware.

## Professor-Facing Title Options

Pick one and then rewrite it slightly in your own style.

1. `Drone-Assisted Wilderness Search and Rescue Using RGB-Thermal Human Detection`
2. `Multimodal UAV Perception for Missing Person Detection in Wilderness Environments`
3. `RGB-Thermal Deep Learning for Search and Rescue from Drone Imagery`

## Why The Previous Idea Felt Common

Your rejected road-damage proposal likely sounded too standard because:
- road damage detection is already a very common student project topic
- the proposal read like a typical "use drone + YOLO + dataset" pipeline
- it named several models without a clear research question
- the novelty depended more on the application setting than on the technical contribution

This new topic is stronger because the technical difficulty is easier to defend:
- small human targets
- occlusion from trees and vegetation
- low-light and poor visibility conditions
- RGB vs thermal trade-offs
- multimodal fusion as a meaningful research question

## Public Datasets

### Primary Dataset: WiSARD

Official site: <https://sites.google.com/uw.edu/wisard/>

Useful points for your own write-up:
- UAV-based wilderness search and rescue dataset
- 26,862 visual images
- 29,989 thermal images
- 15,453 synchronized visual-thermal pairs
- collected in different terrain, weather, and lighting conditions

### Backup Dataset: SeaDronesSee

Official site: <https://seadronessee.cs.uni-tuebingen.de/dataset>

Useful points for your own write-up:
- maritime search and rescue UAV benchmark
- object detection v2 split: 8,930 train, 1,547 val, 3,750 test images
- good fallback if wilderness dataset preparation becomes harder than expected

## Part A Support

### What To Emphasize In The Proposal

- The project targets emergency response, not a routine inspection task.
- The main research question is whether multimodal UAV perception improves person detection reliability in difficult environments.
- The work compares models, not just one detector.
- The project includes image processing before deep learning, not only end-to-end training.
- The GUI makes the system usable for operators during a rescue scenario.

### Abstract Worksheet

Use the structure below to write your own abstract. Keep it around 180 to 220 words.

1. **Problem sentence**
   State why wilderness search and rescue is difficult, slow, expensive, and safety-critical.
2. **Technical gap sentence**
   Explain why RGB-only aerial detection is unreliable under occlusion, low light, or cluttered backgrounds.
3. **Project sentence**
   Introduce a UAV-based system that processes RGB and thermal imagery to detect missing persons.
4. **Method sentence**
   Mention image processing plus deep learning comparison:
   thermal normalization, contrast enhancement, denoising, RGB-only baseline, thermal-only baseline, multimodal fusion.
5. **Dataset sentence**
   State that the project uses public benchmark datasets such as WiSARD, with SeaDronesSee as backup if needed.
6. **Outcome sentence**
   Say the project aims to improve detection robustness and provide a usable decision-support interface for operators.

### Part A Talking Points For Consultation

- "Our previous topic was too common, so we shifted to a higher-impact rescue problem."
- "The key research question is whether RGB-thermal fusion improves detection in challenging environments."
- "We will use public datasets first so the project is achievable, then add a small live-demo component only if hardware is available."
- "The contribution is not just detection. We also include image enhancement, model comparison, and an operator-facing GUI."

## Part B Implementation And Development Plan

### Phase 1: Dataset Study And Feasibility
- inspect WiSARD label format and sample images
- confirm train/validation/test workflow
- identify image-processing steps for RGB and thermal images
- decide whether WiSARD alone is enough or SeaDronesSee is needed as backup

### Phase 2: Baseline Models
- train one RGB-only baseline detector
- train one thermal-only baseline detector
- record precision, recall, F1, and mAP

### Phase 3: Multimodal Improvement
- align RGB and thermal pairs where available
- test a simple fusion strategy
- compare against the single-modality baselines

### Phase 4: Image Processing Study
- test CLAHE or contrast enhancement
- test denoising on thermal imagery
- test resizing or tiling strategy for small-object visibility
- report whether preprocessing improves detection metrics

### Phase 5: GUI Prototype
- build a lightweight web or desktop interface
- allow image or video upload
- display detection boxes, confidence scores, and alert labels
- export a simple result summary

### Phase 6: Demo And Final Validation
- prepare prerecorded examples for guaranteed demo
- optionally connect a live camera or drone feed if available
- record failure cases and discussion points for the final presentation

## Model Comparison Plan

The comparison should stay simple enough to finish, but strong enough to defend.

### Recommended Experimental Setup

**Experiment A: RGB-only baseline**
- input: RGB images only
- goal: establish standard aerial detection performance

**Experiment B: Thermal-only baseline**
- input: thermal images only
- goal: test robustness in poor visibility and low-light conditions

**Experiment C: RGB-thermal fusion**
- input: paired RGB and thermal images
- goal: test whether multimodal fusion improves recall and robustness

### Suggested Model Choices

Choose a final set your team can actually train and explain.

- `YOLO` family model for a strong baseline
- `RT-DETR` or another transformer-style detector for comparison
- a simple early-fusion or late-fusion multimodal approach for the final experiment

### Metrics To Report

- precision
- recall
- F1-score
- mAP
- qualitative failure cases under occlusion or poor lighting

### What Not To Do

- do not promise too many architectures
- do not list five or six models just to sound advanced
- do not claim real-time onboard deployment unless you actually test it

## Image Processing Component

To satisfy the "including image processing" part, explicitly include preprocessing experiments such as:
- CLAHE or local contrast enhancement
- thermal intensity normalization
- Gaussian or median denoising
- gamma correction for dark RGB scenes
- tiling or cropping for small-object detection

Your report should then discuss whether these steps help or hurt model performance.

## GUI Concept

### Recommended GUI

A lightweight rescue monitoring dashboard is enough. It does not need to be complex.

### Core Screens

**1. Upload and input screen**
- upload image or video
- choose RGB, thermal, or fusion mode
- select model

**2. Detection result screen**
- show bounding boxes on frames
- show confidence score for each detection
- highlight high-priority detections

**3. Summary screen**
- total detections
- suspicious frames
- exportable result log

### Nice-To-Have Features

- timeline slider for video review
- side-by-side RGB and thermal view
- toggle to show preprocessing on or off

## Demo Strategy

### Guaranteed Demo Path

Use prerecorded benchmark images or videos so the demo always works.

Recommended flow:
1. load a sample UAV clip or image set
2. run baseline model
3. run fusion model
4. compare detections visually in the GUI
5. show one success case and one failure case

### Optional Hardware Bonus

If your team later gets access to a drone, mobile robot, or camera feed:
- use it only as a bonus demo
- do not make hardware a dependency for project completion
- frame it as a proof-of-concept input source, not as your main evaluation method

## Risks And Mitigations

### Risk 1: Dataset preparation is harder than expected
- mitigation: start from WiSARD samples immediately
- mitigation: keep SeaDronesSee as a backup search-and-rescue dataset

### Risk 2: Fusion model takes too long
- mitigation: finish RGB-only and thermal-only baselines first
- mitigation: implement a simple late-fusion method before trying more advanced fusion

### Risk 3: Compute resources are limited
- mitigation: train on resized data or smaller subsets first
- mitigation: prioritize a strong baseline plus one meaningful improvement

## Recommended Team Positioning

When you talk to the professor, present the project like this:

"We moved away from road-damage inspection because it felt too common. Our new project focuses on multimodal UAV search and rescue, where the research question is whether RGB and thermal fusion can improve missing-person detection in difficult outdoor environments. The project uses public benchmark datasets first, includes image-processing experiments, compares multiple deep-learning approaches, and ends with a practical GUI for rescue support."

## Immediate Next Steps

1. Confirm WiSARD as the main dataset.
2. Check annotation format and download effort.
3. Rewrite the title and abstract in your own words.
4. Get tutor or professor feedback on the topic before you invest in implementation.
