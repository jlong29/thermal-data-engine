## TASK_BRIEF

### Task
- Deliver the thermal-owned downstream handoff for the incoming video folder in two phases: a phase 1 Ultralytics-style image dataset and a phase 2 temporal video-clip package.

### Why this update
- The Xavier NX edge node needed to become a stable producer for the desktop training node without absorbing desktop-side training logic.
- The user wanted an immediate trainable package first, while preserving a path toward track-aware temporal downstream work.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary.
- Preserve stable bundle contents: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Treat future package-contract changes as explicit cross-node contract work, not casual local edits.

### Goal
- Let an operator process a directory of MP4 files on the Xavier NX and produce:
  - a validated phase 1 image-dataset package for immediate desktop YOLO smoke training
  - a validated phase 2 temporal package for provenance-rich downstream inspection and future tracking-aware work

### Success criteria
- [x] Phase 1 directory-processing CLI path exists.
- [x] Phase 1 emits one combined Ultralytics-style package under `outputs/thermal_data_engine/ultralytics_packages/`.
- [x] Phase 1 package validates structurally on-device.
- [x] Phase 1 package was accepted by the desktop consumer and passed single-GPU plus 3-GPU smoke training.
- [x] Phase 2 package format preserves temporal structure, clip provenance, and track continuity strongly enough for downstream inspection.
- [x] Phase 2 package generation path exists in `thermal-data-engine`.
- [x] Phase 2 package validates structurally on-device.
- [x] Phase 2 package was accepted by the desktop consumer as the current inspectable temporal contract.

### Relevant files (why)
- `src/thermal_data_engine/cli.py` — user-facing command surface for `process-directory` and `process-directory-video`
- `src/thermal_data_engine/edge/pipeline.py` — folder processing, package assembly, and fallback windowing logic
- `src/thermal_data_engine/common/models.py` — stable metadata for bundle and package contracts
- `src/thermal_data_engine/vision_api/client.py` — resilient polling against the detector/runtime boundary
- `tests/test_pipeline.py` — regression coverage for package assembly and config handling
- `tests/test_inspect.py` — structural validation coverage for the temporal package
- `README.md` — operator-facing workflow and handoff guidance

### Verification
- Fast: `python3 -m compileall src tests`
- Full: `python3 -m pytest tests`
- Phase 1 package check: `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect ultralytics-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample`
- Phase 2 package check: `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect video-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/video_packages/incoming-video-sample`
- Desktop acceptance evidence: `../vision-trainer/docs/handoffs/DESKTOP_TO_EDGE.md`

### Risks / gotchas
- Desktop acceptance proved the current contracts, but future manifest/layout changes should be routed through the shared contract docs and validators instead of being improvised here.
- The current phase 2 package is accepted as a provenance-rich temporal substrate, not yet as a direct YOLO training contract.

### Deferred work note
- Do not redesign the train/val split strategy here.
- Do not move detector/runtime ownership out of `vision_api` in this task.
- Do not treat phase 2 as directly trainable until a desktop-side converter or consumer is added explicitly.
