# Part A Rewrite Guide

This note gives feedback on the rejected proposal and helps your team rewrite Part A in your own words.
Do not submit this file directly.

## Main Shift

Move from:
- road or infrastructure damage inspection

To:
- multimodal UAV search and rescue for missing-person detection

## Why This New Version Sounds Stronger

The new direction is stronger because it has:
- a less common application area
- a clear research question
- a natural role for image processing
- a meaningful model comparison
- a practical GUI story for final demo and presentation

## What To Keep From The Old Proposal Style

Keep these good proposal habits:
- explain the real-world problem first
- connect the topic to safety and operational efficiency
- mention the full end-to-end pipeline
- show that the output supports decision-making

## What To Remove

Avoid these patterns in the new abstract:
- listing many model names in one sentence
- sounding like the main contribution is just "use a drone"
- promising hardware access too early
- spending too much space on future features like mapping and reporting

## Better Framing

The strongest framing for the new abstract is:
- problem importance
- why the problem is hard
- what your system does
- what data you will use
- what comparison you will perform
- what practical value the result provides

## Sentence-Level Rewrite Plan

### Sentence 1
Describe the operational problem.

Focus on:
- time-critical rescue operations
- risk to human search teams
- large and visually complex search areas

### Sentence 2
Explain the technical difficulty.

Focus on:
- small human targets
- cluttered natural backgrounds
- occlusion
- poor lighting and visibility

### Sentence 3
Introduce your proposed system.

Focus on:
- UAV imagery
- RGB and thermal sensing
- deep-learning-based missing-person detection

### Sentence 4
State the technical method.

Focus on:
- image preprocessing
- RGB-only baseline
- thermal-only baseline
- multimodal fusion comparison

### Sentence 5
State the data source and evaluation plan.

Focus on:
- public datasets
- benchmark-driven evaluation
- metrics such as precision, recall, F1, and mAP

### Sentence 6
Close with practical impact.

Focus on:
- improved robustness
- decision support for rescue operators
- deployable GUI concept

## Phrases To Avoid

- "The project uses YOLO, DETR, U-Net..."
- "A drone will follow a predefined flight path..."
- "The system will automatically solve..."
- "We request access to the lab..." in the main abstract

These make the abstract sound unfocused or operationally dependent.

## What The Professor Should Hear

Your rewrite should make the professor think:
- this team changed to a harder and more original topic
- this project has a clear comparison study
- this is achievable with public datasets
- the team understands both research value and practical deployment

## Quick Self-Check Before Submission

If your final abstract answers all six questions below, it is probably in good shape:

1. What problem are we solving?
2. Why is it difficult in computer vision terms?
3. What is our proposed system?
4. What is the actual research question?
5. What public data will we use?
6. What practical output will we demonstrate?
