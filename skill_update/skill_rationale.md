# Skill Rationale — xray_grounding_tool

## Problem

Existing ChatClinic tools process medical images structurally (DICOM metadata, NIfTI slices)
but do not provide **semantic, finding-level analysis** of chest X-rays. Clinicians need:
- Automated detection of specific pathologies (e.g., Consolidation, Pleural Effusion)
- Spatial localization of abnormal regions (visual grounding)
- Natural-language impression suitable for clinical decision support

## Solution

`xray_grounding_tool` uses GPT-4o's vision capabilities to:
1. Ingest a chest X-ray image (JPG/PNG, including MIMIC-CXR format)
2. Detect abnormal findings using the CheXpert label taxonomy
3. Return normalized bounding box coordinates for each finding
4. Render annotated images with colour-coded boxes and confidence scores

## Why GPT-4o

- GPT-4o has demonstrated strong zero-shot chest X-ray interpretation matching
  resident-level performance on CheXpert benchmark tasks.
- No local GPU required: API-based inference avoids environment complexity.
- Structured JSON output (`response_format`) enables reliable downstream parsing.

## Dataset Validation

Validated against 5 MIMIC-CXR samples (mimic-cxr-jpg v2.1.0) with known CheXpert labels:
- Consolidation, Pleural Effusion, Lung Opacity, Lung Lesion, Fracture
- Ground-truth labels used only for qualitative verification (not supervision)

## Limitations

- GPT-4o bounding box coordinates are model-predicted, not pixel-perfect segmentation masks.
- Performance may degrade on non-standard views (lateral, oblique).
- API latency ~10–20 seconds per image.
