## TASK_BRIEF

### Task
- Deliver the thermal-owned downstream handoff in two phases for the incoming video folder:
  1. an image-dataset package for immediate Ultralytics smoke testing
  2. a video-clip dataset package that preserves temporal structure strongly enough for downstream tracking-aware fine-tuning experiments

### Why this update
- The user wants package generation on-device to be separated cleanly from downstream model evaluation on the hotter machine.
- The image-dataset package is the fastest path to an initial YOLO smoke test, but it intentionally flattens video into labeled frames.
- The broader thermal-data goal still includes leveraging temporal structure from videos, so the next package phase should explicitly preserve clip and track continuity instead of letting that objective drift.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary instead of re-embedding DeepStream control logic here.
- Preserve stable bundle contracts: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer bounded, inspectable validation flows over hidden background behavior.
- Treat the current per-job `vision_api` dataset package as the compatibility reference for image-dataset handoff.
- Treat temporal structure as a first-class downstream concern for phase 2 rather than assuming the flat image package is the final ownership boundary.

### Goal
- Let an operator point `thermal-data-engine` at a folder of MP4 files and receive:
  - phase 1: one inspectable Ultralytics-style image dataset with provenance
  - phase 2: one inspectable video-clip-oriented dataset package that preserves temporal relationships, clip provenance, and track context for downstream evaluation

### Downstream evaluation split
- My job: create the packages on-device, validate their structure, and document the handoff paths.
- User's job: evaluate each package on the hotter machine within the YOLO fine-tuning workflow.
- Decision boundary: phase 1 should be evaluated first. Phase 2 should be judged after the user inspects the image-dataset smoke-test outcome, unless the user explicitly asks for both in parallel.

### Success criteria
- [x] Phase 1 image-package CLI path exists for processing a directory of videos.
- [x] Phase 1 assembles one combined Ultralytics-style package under `outputs/thermal_data_engine/ultralytics_packages/`.
- [x] Phase 1 package contents stay structurally compatible with the existing `inspect ultralytics-package` validator.
- [x] Phase 1 incoming sample folder has been processed end to end against live `vision_api`.
- [x] Phase 1 resulting combined package is validated and ready for desktop handoff.
- [ ] Phase 1 downstream smoke test on the hotter machine is evaluated by the user and any concrete incompatibility is recorded.
- [ ] Phase 2 package format is defined explicitly enough that temporal structure, clip provenance, and track continuity are preserved rather than flattened away.
- [ ] Phase 2 package generation path exists in `thermal-data-engine`.
- [ ] Phase 2 package is created from the incoming folder and validated structurally on-device.
- [ ] Phase 2 downstream smoke test or fit-for-purpose evaluation is performed by the user on the hotter machine.

### Relevant files (why)
- `src/thermal_data_engine/cli.py` — user-facing command surface
- `src/thermal_data_engine/edge/pipeline.py` — batch processing and package assembly
- `src/thermal_data_engine/edge/tracking.py` — current tracking baseline and future temporal upgrade surface
- `src/thermal_data_engine/common/models.py` — stable metadata for bundle/package contracts
- `tests/test_pipeline.py` — focused regression coverage for folder processing
- `README.md` — operator-facing run and handoff instructions

### Two-phase plan
#### Phase 1, image datasets
1) Keep the folder-processing and image-package assembly path working with deterministic output layout.
2) Validate the package against the repo-local Ultralytics inspector.
3) Hand the validated image package to the user for hotter-machine smoke testing.
4) Reopen phase 1 only if the downstream consumer reports a concrete incompatibility.

#### Phase 2, video clip datasets
1) Define the package contract for temporally meaningful clip handoff.
2) Decide what metadata and layout the downstream training/evaluation flow needs, for example clip boundaries, frame ordering, track ids, and manifest-level provenance.
3) Upgrade the current simplistic tracking-preservation story as needed, potentially including a stronger tracker than the present `iou_greedy_v1` baseline if the evidence says it materially improves the package.
4) Generate one real phase 2 package from `datasets/incoming` and validate it on-device before desktop handoff.

### Small change sets (execution order)
1) Keep `process-directory` and the image-package path stable.
2) Record the downstream result of the phase 1 image smoke test.
3) Specify the phase 2 video-clip package contract and acceptance checks.
4) Implement the phase 2 package generation path.
5) Run the phase 2 package creation on `datasets/incoming` and validate it before handoff.

### Verification
#### Phase 1
- Fast: `python3 -m compileall src tests`
- Targeted: `python3 -m pytest tests/test_pipeline.py`
- Full: `python3 -m pytest tests`
- Live: `PYTHONPATH=src python3 -m thermal_data_engine.cli process-directory --source-dir ~/.openclaw/workspace/datasets/incoming --edge-config configs/edge/training_sample.yaml --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000 --package-name incoming-training-sample`
- Package check: `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect ultralytics-package --path ~/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample`

#### Phase 2
- To be defined in the repo before claiming a desktop-ready temporal package.

### Blockers
- None for phase 1 package creation.
- Phase 2 is intentionally blocked on defining the temporal handoff contract clearly enough that downstream evaluation is meaningful instead of accidental.

### Risks / gotchas
- Multiple per-job dataset packages can reuse filenames like `bounded_input_frameXXXX.jpg`, so the combined phase 1 package must rename entries deterministically to avoid collisions.
- `vision_api` being reachable on port `8000` is a better truth test than probing `/health`; this host currently serves docs on `8000` while `/health` still returns `404`.
- The outer `process-directory` CLI can be interrupted after the per-file `vision_api` jobs finish but before the final combined package is written, which can leave an empty run directory for the last source while the per-job dataset package itself is already complete.
- The current image package is useful for a first fine-tuning smoke test, but it does discard temporal ordering as a training primitive.
- The current tracker is still a simple `iou_greedy_v1` baseline, so phase 2 should not overclaim temporal quality until the package contract and tracker needs are tested honestly.

### Decision rule for defaults
- Default phase 1 to processing all supported video files in the source directory in sorted order and emit one combined image package rooted under `ultralytics_packages/`.
- Do not claim a default phase 2 package shape until the temporal contract is explicitly written down.

### Handoff result so far
- Phase 1 live batch evidence now exists at `outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample/`.
- Phase 1 package validation passed with `1519` images, `1519` labels, `1215` train entries, and `304` val entries across the three incoming MP4 files.
- Source provenance is captured in `outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample/manifest.json`.
- Phase 1 is ready for the user's hotter-machine smoke test.

### Deferred work note
- Do not redesign train/val split strategy beyond preserving each source package's split assignments in the combined phase 1 package.
- Do not move detector/runtime ownership out of `vision_api` in this task.
- Do not treat phase 1 image-package success as proof that the temporal/video objective is complete.
