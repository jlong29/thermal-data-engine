# Boundary and Ultralytics Notes

This note captures a refinement that emerged during live validation of `thermal-data-engine` on the Xavier NX.

## Why this note exists

Two related questions came up during validation:

1. What exactly must conform to Ultralytics YOLO11 training expectations?
2. Where should the boundary live between `vision_api` and `thermal-data-engine`?

The answer is that we should be strict about the **Ultralytics training-facing dataset package**, but we should not force every internal edge artifact to look like a YOLO training dataset.

## Key distinction: training package vs edge bundle

### Ultralytics-facing training package
This is the dataset that a future Ultralytics YOLO11 fine-tuning run should consume.

For object detection, the relevant Ultralytics expectation is the standard YOLO detect dataset format:

- a dataset YAML with keys like `path`, `train`, `val`, and `names`
- one label `.txt` per image
- one row per object in `class x_center y_center width height` format
- normalized `xywh` coordinates in `[0, 1]`
- zero-indexed class ids
- train/val may point either to directories or to text files listing image paths

This is the place where we should be strict.

### Edge-side operational bundle
This is the retained edge artifact contract used by `thermal-data-engine`.

Current stable bundle contents:

- `clip.mp4`
- `detections.parquet`
- `tracks.parquet`
- `clip_manifest.json`

This bundle is for edge inspection, downstream triage, and later handoff. It does **not** need to match the Ultralytics dataset spec directly.

## Current state of the codebase

### What `vision_api` currently does
`vision_api` currently owns more than pure inference/runtime behavior. It already handles:

- bounded inference job creation and status tracking
- structured detections export
- dataset package creation under `outputs/inference_jobs/<job_id>/dataset/`
- optional preview rendering

This includes writing:

- `dataset/images/*.jpg`
- `dataset/labels/*.txt`
- `dataset/splits/train.txt`
- `dataset/splits/val.txt`
- `dataset/dataset.yaml`
- `dataset/manifest.json`

The current dataset packaging implementation is clearly based on the standard Ultralytics YOLO detect layout.

### What `thermal-data-engine` currently does
`thermal-data-engine` currently owns:

- edge-side config and operator workflow
- `vision_api` job submission/polling through a narrow client boundary
- detection ingestion from `detections.jsonl`
- tracking and selection policy
- retained bundle writing
- inspection tooling over retained runs and bundles

## Recommended architectural boundary

### `vision_api` should own
`vision_api` should remain the narrow local inference/runtime control plane.

That means responsibility for:

- model/runtime selection
- bounded job submission
- job lifecycle and status
- health and telemetry endpoints
- DeepStream invocation and logs
- structured raw outputs needed by downstream consumers

Concretely, its durable outputs should center on:

- `request.json`
- `status.json`
- `manifest.json`
- `logs/`
- `detections.jsonl`
- detector summaries and other runtime diagnostics
- bounded runtime input clip if that remains useful as a downstream source artifact

### `thermal-data-engine` should own
`thermal-data-engine` should own downstream interpretation and packaging.

That means responsibility for:

- consuming structured detections from `vision_api`
- tracking and selection
- retained edge bundles
- operator inspection tools
- training-oriented dataset packaging for downstream fine-tuning workflows
- optional preview/inspection artifacts when they are part of downstream data curation rather than detector-runtime debugging

In other words:

- `vision_api` should answer: **can we run bounded inference jobs safely and reproducibly?**
- `thermal-data-engine` should answer: **what do we keep, how do we package it, and what do downstream consumers train or inspect?**

## Why this split is better

This boundary fits the repo missions better.

### Reasons to move packaging out of `vision_api`
- Dataset packaging is downstream data interpretation, not detector-runtime control.
- `thermal-data-engine` already owns selection, retention, and bundle semantics, so packaging belongs near that logic.
- It avoids making `vision_api` the place where every downstream artifact concern accumulates.
- It creates a cleaner future where multiple downstream packagers could consume the same `vision_api` job outputs.

### Reasons not to move everything at once
- The current path works and is valuable as validation evidence.
- We are still separating structure/invariants validation from artifact correctness validation.
- A large move right now would mix architecture cleanup with active artifact debugging.

## Recommended migration strategy

Do this as a staged refactor.

### Stage 1, document the boundary and keep current behavior
- Keep current `vision_api` dataset packaging working.
- Treat it as the existing compatibility reference for Ultralytics-style export.
- Finish the current validation pass without claiming the architecture is final.

### Stage 2, add packaging capability to `thermal-data-engine`
Build a thermal-side export path that consumes:

- `detections.jsonl`
- `vision_api` job metadata/manifest
- bounded runtime input clip or source clip path

and writes:

- YOLO-format images/labels
- `splits/train.txt`
- `splits/val.txt`
- `dataset.yaml`
- thermal-owned dataset manifest / provenance metadata

### Stage 3, reduce `vision_api` packaging responsibility
After thermal-side packaging is validated:

- de-emphasize or remove dataset packaging from `vision_api`
- keep `vision_api` focused on inference/runtime artifacts and raw structured outputs
- preserve backward compatibility long enough to avoid breaking live workflows abruptly

## Acceptance implications

This boundary refinement also reinforces a workflow lesson:

- structure/plumbing validation is one layer
- artifact correctness is a stricter layer
- architecture cleanup is yet another layer

We should not mix them casually.

A working current package path is still useful, even if we later decide the ownership boundary should move.

## Provisional decision

The current best direction is:

- keep `vision_api` as the inference/runtime/job-control boundary
- move dataset packaging and related downstream data-shaping responsibilities toward `thermal-data-engine`
- do the migration in stages, using the current `vision_api` packaging path as a compatibility reference rather than pretending it is the final architecture

## Follow-up work

1. Add a repo-local task for thermal-side YOLO package export.
2. Define the exact handoff contract from `vision_api` to `thermal-data-engine`.
3. Compare the new thermal-side export against the current `vision_api` package output.
4. Validate the thermal-owned package with a real Ultralytics load/train smoke test before retiring the old path.
