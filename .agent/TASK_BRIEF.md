## TASK_BRIEF

### Task
- Close out the current `thermal-data-engine` validation slice by separating completed structure/invariants work from the remaining artifact-correctness follow-up, while preparing the next thermal-owned Ultralytics-compatible packaging slice.

### Why this update
- The user completed a real on-device walkthrough of the new Quick start and confirmed the lower-memory bring-up path is usable.
- That walkthrough proved the structure/invariants layer, but it also exposed a likely artifact-level issue in retained bundle clip timing metadata.
- The user also approved the architectural direction that `vision_api` should stay focused on inference/runtime/job control while downstream data packaging should migrate toward `thermal-data-engine` in a staged way.
- Overnight work should therefore focus on bounded, high-signal progress that sets up tomorrow's hotter-machine Ultralytics smoke test without overclaiming what is already done.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary instead of re-embedding DeepStream control logic here.
- Preserve stable bundle contracts: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer bounded, inspectable validation flows over hidden background behavior.
- Do not collapse structure/plumbing validation into artifact-correctness claims.
- Do not break the current `vision_api` dataset-packaging path until a thermal-owned replacement is validated against it.

### Goal
- Treat structure/invariants validation as complete, close the remaining artifact-correctness gap honestly, and push the thermal repo toward owning the downstream Ultralytics-compatible dataset packaging contract.

### Success criteria
- [x] A named lower-memory or fallback edge config/profile exists.
- [x] The profile is documented clearly enough that operators know when to use it.
- [x] The smoke-test or bounded validation path can exercise the lower-memory profile.
- [x] Human-facing setup docs now cover the required virtualenv/editable-install path and how to start `vision_api`.
- [x] Structure/invariants validation is recorded as complete for the current slice: package install works on-device, CLI help surfaces are correct, default and low-memory smoke tests reach local `vision_api`, and run records / inspect outputs are coherent.
- [x] The repo brief states explicitly that preview artifacts are optional and that missing preview output is not a correctness failure when preview was not requested.
- [x] A durable repo doc captures the Ultralytics boundary and the staged migration rationale. (`docs/BOUNDARY_AND_ULTRALYTICS_NOTES.md`)
- [x] Artifact correctness is resolved for at least one retained bundle, including sane clip timing/media metadata and consistency between `clip.mp4`, parquet artifacts, and `clip_manifest.json`, or the issue is converted into a concrete follow-up/handoff with clear evidence.
- [x] The thermal repo has a concrete Ultralytics-compatibility checklist or validation helper for the training-facing package boundary, ready for tomorrow's hotter-machine smoke test. (`inspect ultralytics-package`, `docs/ULTRALYTICS_PACKAGE_CHECKLIST.md`)
- [x] The next thermal-owned packaging slice is concrete on disk, either as validated implementation scaffolding or as a precise handoff contract and file plan that can be executed without re-deciding the boundary. (`docs/ULTRALYTICS_PACKAGE_CHECKLIST.md`)

### Relevant files (why)
- `configs/edge/default.yaml` — current conservative baseline
- `configs/edge/low_memory.yaml` — explicit fallback bring-up profile
- `src/thermal_data_engine/cli.py` — smoke-test, process-file, and inspect entrypoints the user validated directly
- `src/thermal_data_engine/edge/pipeline.py` — run creation, selection, bundle writing, and artifact behavior
- `src/thermal_data_engine/common/models.py` — stable retained-bundle schema
- `docs/BOUNDARY_AND_ULTRALYTICS_NOTES.md` — durable boundary and migration rationale
- `README.md` — human-facing Quick start and operator guidance
- `tests/` — focused regression or config coverage

### Current acceptance framing
1) Structure/invariants, completed layer
   - Setup, CLI discoverability, config selection, `vision_api` connectivity, run-record writing, selection metadata, and inspect tooling are validated on-device.
   - Keep this recorded as completed, not silently reopened.
2) Artifact correctness, active layer
   - Validate at least one retained bundle end to end for human-usable outputs.
   - Confirm bounded `clip.mp4` timing/media metadata is believable, parquet outputs match manifest counts/expectations, and optional artifacts are interpreted according to request flags rather than assumed.
3) Packaging-boundary preparation, next layer
   - Make the thermal-owned Ultralytics-compatible export path concrete enough that tomorrow's hotter-machine smoke test has a clear package contract to validate.

### Overnight plan
1) Keep the completed structure/invariants evidence intact. (done)
2) Diagnose the retained-bundle clip timing issue precisely, including whether absolute source timestamps are being passed to ffmpeg when runtime-relative timestamps are needed. (done, regenerated retained bundle confirmed sane)
3) Add or refine durable notes/checks for the Ultralytics-compatible training-facing package boundary, using the current `vision_api` package as the compatibility reference rather than the final architecture. (done)
4) Prepare the next thermal-owned packaging slice so work can start or continue without boundary ambiguity, but do not rip packaging out of `vision_api` in one jump. (done)
5) Defer the real Ultralytics load/train smoke test until the hotter machine is ready tomorrow, but leave the package contract and checklist ready for it. (ready, structural validator confirmed against a real reference dataset package)

### Verification
- Fast: `python3 -m compileall src`
- Targeted: `python3 -m pytest tests`
- Structure layer evidence:
  - `python3 -m thermal_data_engine.cli --help`
  - `python3 -m thermal_data_engine.cli smoke-test --help`
  - `python3 -m thermal_data_engine.cli smoke-test --source "$SOURCE" --output-root "$OUT" --vision-api-url http://127.0.0.1:8000 --max-duration-sec 3.0`
  - `python3 -m thermal_data_engine.cli smoke-test --source "$SOURCE" --edge-config configs/edge/low_memory.yaml --output-root "$OUT" --vision-api-url http://127.0.0.1:8000 --use-edge-window`
  - `python3 -m thermal_data_engine.cli inspect recent --root "$OUT"`
- Artifact layer:
  - `ffprobe <bundle>/clip.mp4`
  - inspect one selected bundle's manifest and parquet outputs
  - confirmed on `outputs/thermal_data_engine/bundles/clip-4c2b3b029292`: `clip.mp4` duration `4.997s` vs manifest window `0.0 -> 4.995`, `detections.parquet` rows `29`, `tracks.parquet` rows `4`, `extra.clip_artifact.timestamp_mode=runtime_relative_timestamps`
- Packaging readiness layer:
  - `python3 -m thermal_data_engine.cli inspect ultralytics-package --path <dataset_root>`
- Tomorrow's hotter-machine validation target:
  - a real Ultralytics dataset load/train smoke test against the training-facing package boundary

### Risks / gotchas
- A lower-memory profile should stay inspectable and bounded, not become a vague collection of emergency flags.
- The fallback profile should not quietly erode the stable bundle contract or detector boundary.
- Smoke-test defaults intentionally provide their own bounded window unless `--use-edge-window` is passed, so operators must opt in when they specifically want to validate a named profile's own runtime window.
- Older Xavier-side virtualenvs may start with packaging tools too old for `pyproject.toml` editable installs; upgrade `pip`, `setuptools`, and `wheel` first.
- A retained bundle can be structurally present while still having suspicious media timing metadata, so inspect results must not be over-read.
- When `clip.mp4` is cut from `vision_api`'s already-bounded `runtime_input_path`, manifest timestamps are still absolute source timestamps. Bundle extraction must convert them back to runtime-relative offsets before calling ffmpeg.
- The current `vision_api` dataset package is the reference for Ultralytics compatibility today, but it should be treated as a compatibility reference, not necessarily the final ownership boundary.
- The new `inspect ultralytics-package` helper is intentionally structural, not a substitute for a real Ultralytics import/train smoke test on the hotter machine.
- Real reference dataset packages may express `dataset.yaml` class names as an indented mapping (`names:\n  0: person`), so the structural validator must accept both list-style and mapping-style Ultralytics name declarations.

### Decision rule for completion
- This repo slice is complete when the artifact-correctness layer is resolved on at least one retained bundle or converted into a concrete follow-up/handoff, and the thermal-owned packaging direction is concrete enough that tomorrow's Ultralytics smoke test has a clear target package contract. Current state: complete for this slice, pending tomorrow's hotter-machine Ultralytics load/train smoke test outside this repo-local brief.

### Deferred work note
- Do not turn this task into model/backend redesign or cross-repo detector tuning unless artifact validation proves the issue cannot be handled from the thermal-data-engine side.
- Do not force a full packaging migration overnight if the result would be under-verified; staged progress is better than a boundary rewrite with weak evidence.
