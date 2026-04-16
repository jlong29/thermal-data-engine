# Closeout: thermal validation slice

## Summary
This repo-local slice closed out the current Xavier NX thermal-data-engine validation increment.

It kept structure/invariants validation explicitly complete, resolved the retained-bundle artifact follow-up on at least one real bundle, and made the next thermal-owned Ultralytics-compatible packaging boundary concrete enough for a hotter-machine smoke test.

## What changed
- Added and documented a lower-memory edge profile and smoke-test validation path.
- Fixed retained bundle clip extraction so bounded runtime clips use runtime-relative timestamps when cutting `clip.mp4` from `vision_api` runtime input artifacts.
- Added a lightweight `inspect ultralytics-package` validator and documented the training-facing package contract in `docs/ULTRALYTICS_PACKAGE_CHECKLIST.md`.
- Recorded the staged architectural boundary: keep `vision_api` focused on inference/runtime/job control, and move downstream packaging toward `thermal-data-engine` gradually.

## Verification evidence
- `python3 -m compileall src`
- `python3 -m pytest tests`
- Real retained-bundle artifact check on `outputs/thermal_data_engine/bundles/clip-4c2b3b029292`:
  - `clip.mp4` duration `4.997s`
  - manifest window `0.0 -> 4.995`
  - `detections.parquet` rows `29`
  - `tracks.parquet` rows `4`
  - `extra.clip_artifact.timestamp_mode=runtime_relative_timestamps`
- Structural package check:
  - `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect ultralytics-package --path /home/myclaw/.openclaw/workspace/outputs/inference_jobs/yolo_20260415_230220_93e12e/dataset`
  - result: `ok: true`

## Acceptance status
- Structure/invariants: complete
- Artifact correctness for one retained bundle: complete
- Thermal-owned packaging contract/checklist: complete for this slice
- Real hotter-machine Ultralytics load/train smoke test: deferred to the next slice

## Follow-up
- Reopen this repo only if the hotter-machine Ultralytics smoke test finds a concrete package incompatibility or if the next staged thermal-owned exporter implementation begins.
