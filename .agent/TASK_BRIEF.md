## TASK_BRIEF

### Task
- Add a first-class folder-to-handoff dataset generation path in `thermal-data-engine`, then run it over `~/.openclaw/workspace/datasets/incoming` so the desktop Ultralytics smoke test can pull one concrete package.

### Why this update
- The next validation step is on the hotter desktop machine, and the handoff should be a real sample package generated from multiple incoming MP4 files, not an implicit collection of one-off per-job outputs.
- The current repo can process one file cleanly, but it does not yet expose a first-class command that takes a folder of videos and emits one combined Ultralytics-style package.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary instead of re-embedding DeepStream control logic here.
- Preserve stable bundle contracts: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer bounded, inspectable validation flows over hidden background behavior.
- Treat the current per-job `vision_api` dataset package as the compatibility reference for the combined handoff package.

### Goal
- Let an operator point `thermal-data-engine` at a folder of MP4 files and receive one inspectable Ultralytics-style package plus provenance about the contributing runs.

### Success criteria
- [x] A repo-local CLI path exists for processing a directory of videos.
- [x] The directory path assembles one combined Ultralytics-style package under `outputs/thermal_data_engine`.
- [x] Combined package contents stay structurally compatible with the existing `inspect ultralytics-package` validator.
- [x] The incoming sample folder has been processed end to end against live `vision_api`.
- [x] The resulting combined package is validated and ready for desktop handoff.

### Relevant files (why)
- `src/thermal_data_engine/cli.py` — user-facing command surface
- `src/thermal_data_engine/edge/pipeline.py` — batch processing and package assembly
- `tests/test_pipeline.py` — focused regression coverage for folder processing
- `README.md` — operator-facing run and handoff instructions

### Refined Phase 2 Plan
1) Add the folder-processing and package-assembly path with deterministic output layout.
2) Cover the new path with a targeted test and document the CLI.
3) Run it against `datasets/incoming`, validate the package, and record the handoff path.

### Small change sets (execution order)
1) `cli.py` + `edge/pipeline.py` for the new `process-directory` workflow
2) `tests/test_pipeline.py` for combined-package coverage
3) `README.md` for the batch handoff command and output contract
4) Live run on `datasets/incoming` plus package validation

### Verification
- Fast: `python3 -m compileall src tests`
- Targeted: `python3 -m pytest tests/test_pipeline.py`
- Full: `python3 -m pytest tests`
- Live: `PYTHONPATH=src python3 -m thermal_data_engine.cli process-directory --source-dir ~/.openclaw/workspace/datasets/incoming --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000 --package-name incoming-sample`
- Package check: `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect ultralytics-package --path ~/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-sample`

### Blockers
- None. The live `vision_api` service was reachable at `http://127.0.0.1:8000` even though `/health` still returned `404`, and the batch handoff package was validated against the real runtime.

### Risks / gotchas
- Multiple per-job dataset packages can reuse filenames like `bounded_input_frameXXXX.jpg`, so the combined package must rename entries deterministically to avoid collisions.
- `vision_api` being reachable on port `8000` is a better truth test than probing `/health`; this host currently serves docs on `8000` while `/health` still returns `404`.
- The outer `process-directory` CLI can be interrupted after the per-file `vision_api` jobs finish but before the final combined package is written, which can leave an empty run directory for the last source while the per-job dataset package itself is already complete.
- Some source videos may yield zero labeled frames; the combined package must still stay inspectable.

### Decision rule for defaults
- Default to processing all supported video files in the source directory in sorted order and emit one combined package rooted under `ultralytics_packages/`.

### Handoff result
- Live batch evidence now exists at `outputs/thermal_data_engine/ultralytics_packages/incoming-sample/`.
- Package validation passed with `29` images, `29` labels, `22` train entries, and `7` val entries across the three incoming MP4 files.
- Source provenance is captured in `outputs/thermal_data_engine/ultralytics_packages/incoming-sample/manifest.json`, including the zero-label `example.mp4` input.

### Deferred work note
- Do not redesign train/val split strategy beyond preserving each source package's split assignments in the combined package.
- Do not move dataset-package ownership fully out of `vision_api` in this task; just provide the thermal-owned batch handoff layer.