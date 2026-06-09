#!/usr/bin/env python3
"""
Demo: GPT-4o X-ray Visual Grounding on 5 MIMIC-CXR samples.

Usage:
    python demo.py

Requires OPENAI_API_KEY to be set, or edit API_KEY below.
"""

import gzip
import csv
import json
import os
import sys
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MIMIC_ROOT = Path("/home/nas5/sangjunpark/mimic/physionet.org/files/mimic-cxr-jpg/2.1.0")
CHEXPERT_CSV = MIMIC_ROOT / "mimic-cxr-2.0.0-chexpert.csv.gz"
FILES_ROOT = MIMIC_ROOT / "files"
OUTPUT_DIR = Path(__file__).parent / "outputs"
N_SAMPLES = 5

if not API_KEY:
    print("Error: OPENAI_API_KEY environment variable is not set.")
    print("  export OPENAI_API_KEY='sk-...'")
    sys.exit(1)

# Add project root to path so plugin.logic is importable
sys.path.insert(0, str(Path(__file__).parent))
from plugin.logic import execute

# ── Helpers ─────────────────────────────────────────────────────────────────

ABNORMAL_LABELS = [
    "Atelectasis", "Cardiomegaly", "Consolidation", "Edema",
    "Enlarged Cardiomediastinum", "Fracture", "Lung Lesion", "Lung Opacity",
    "Pleural Effusion", "Pleural Other", "Pneumonia", "Pneumothorax",
]


def load_abnormal_samples(n: int = 5) -> list[dict]:
    """Return up to n rows from CheXpert CSV that have at least one positive label."""
    samples = []
    with gzip.open(CHEXPERT_CSV, "rt") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pos = {k: v for k, v in row.items() if k in ABNORMAL_LABELS and v == "1.0"}
            if pos:
                samples.append({
                    "subject_id": row["subject_id"],
                    "study_id": row["study_id"],
                    "labels": list(pos.keys()),
                })
            if len(samples) >= n:
                break
    return samples


def find_pa_image(subject_id: str, study_id: str) -> Path | None:
    """Find the first JPG for a given subject/study (prefer PA view filename)."""
    pref = f"p{subject_id[:2]}"
    study_dir = FILES_ROOT / pref / f"p{subject_id}" / f"s{study_id}"
    if not study_dir.exists():
        return None
    jpgs = sorted(study_dir.glob("*.jpg"))
    return jpgs[0] if jpgs else None


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = load_abnormal_samples(N_SAMPLES)

    if not samples:
        print("No abnormal samples found in MIMIC dataset.")
        return

    print(f"Found {len(samples)} abnormal samples. Running GPT-4o analysis...\n")
    all_results = []

    for i, sample in enumerate(samples, 1):
        subj = sample["subject_id"]
        study = sample["study_id"]
        gt_labels = sample["labels"]

        print(f"[{i}/{len(samples)}] Subject {subj} | Study {study}")
        print(f"  Ground-truth labels: {', '.join(gt_labels)}")

        img_path = find_pa_image(subj, study)
        if img_path is None:
            print(f"  [SKIP] Image not found.\n")
            continue

        result = execute({
            "image_path": str(img_path),
            "save_annotated": True,
            "output_dir": str(OUTPUT_DIR),
            "api_key": os.environ["OPENAI_API_KEY"],
        })

        if result.get("error"):
            print(f"  [ERROR] {result['error']}\n")
            continue

        status = "ABNORMAL" if result["abnormal"] else "NORMAL"
        print(f"  GPT verdict : [{status}]")
        print(f"  Impression  : {result['impression']}")
        for f in result["findings"]:
            print(f"    - {f}")
        if result["bounding_boxes"]:
            print(f"  Bounding boxes ({len(result['bounding_boxes'])}):")
            for bb in result["bounding_boxes"]:
                print(f"    [{bb['label']}] ({bb['x1']:.2f},{bb['y1']:.2f}) -> ({bb['x2']:.2f},{bb['y2']:.2f})  conf={bb['confidence']:.0%}")
        if result.get("annotated_image_path"):
            print(f"  Annotated   : {result['annotated_image_path']}")
        print()

        all_results.append({
            "subject_id": subj,
            "study_id": study,
            "image_path": str(img_path),
            "ground_truth": gt_labels,
            **result,
        })

    # Save full JSON report
    report_path = OUTPUT_DIR / "demo_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Full report saved to: {report_path}")


if __name__ == "__main__":
    main()
