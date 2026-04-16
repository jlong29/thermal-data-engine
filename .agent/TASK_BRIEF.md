## TASK_BRIEF

### Task
- Validate the new lower-memory `thermal-data-engine` bring-up path with explicit layered acceptance: first structure/invariants, then artifact correctness.

### Why this update
- The lower-memory profile and smoke-test workflow now exist, and the user is validating them directly from the README Quick start on-device.
- The current validation pass clarified an important acceptance distinction: a run can prove the CLI, config loading, `vision_api` boundary, run-record writing, and inspect tooling are structurally correct without yet proving that every emitted artifact is human-usable and semantically correct.
- We want the brief to reflect both the immediate repo work and how we are reasoning about acceptance together, so future turns do not overclaim completion.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary instead of re-embedding DeepStream control logic here.
- Preserve stable bundle contracts: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer bounded, inspectable validation flows over hidden background behavior.
- Do not collapse structure/plumbing validation into artifact-correctness claims.

### Goal
- Confirm that operators can reliably exercise the lower-memory path and the repo's bounded validation surface, while explicitly tracking artifact correctness as a stricter follow-up gate rather than an implied side effect of structural success.

### Success criteria
- [x] A named lower-memory or fallback edge config/profile exists.
- [x] The profile is documented clearly enough that operators know when to use it.
- [x] The smoke-test or bounded validation path can exercise the lower-memory profile.
- [x] Human-facing setup docs now cover the required virtualenv/editable-install path and how to start `vision_api`.
- [x] Structure/invariants validation passes for the current slice: package install works on-device, CLI help surfaces are correct, default and low-memory smoke tests can reach local `vision_api`, and run records / inspect outputs are coherent.
- [x] The repo brief now states explicitly that preview artifacts are optional and that missing preview output is not a correctness failure when preview was not requested.
- [ ] Artifact correctness is tracked as a separate acceptance layer for at least one retained bundle, including sane clip timing/media metadata and consistency between `clip.mp4`, parquet artifacts, and `clip_manifest.json`.
- [ ] If artifact-level issues point across the repo boundary, the follow-up is handed off cleanly instead of being silently absorbed into a vague repo-local success claim.

### Relevant files (why)
- `configs/edge/default.yaml` — current conservative baseline
- `configs/edge/low_memory.yaml` — explicit fallback bring-up profile
- `src/thermal_data_engine/cli.py` — smoke-test, process-file, and inspect entrypoints the user is validating directly
- `src/thermal_data_engine/edge/pipeline.py` — run creation, selection, bundle writing, and validation behavior
- `README.md` — human-facing Quick start and operator guidance now used for live validation
- `tests/` — focused regression or config coverage

### Current acceptance framing
1) Structure/invariants, current layer
   - Validate setup, CLI discoverability, config selection, `vision_api` connectivity, run-record writing, selection metadata, and inspect tooling.
   - Treat these as necessary conditions for progress, not as proof that retained artifacts are already correct in every detail.
2) Artifact correctness, next layer
   - Validate at least one retained bundle end to end for human-usable outputs.
   - Confirm bounded `clip.mp4` timing/media metadata is believable, parquet outputs match manifest counts/expectations, and optional artifacts are interpreted according to request flags rather than assumed.

### Refined plan
1) Keep the new lower-memory profile and human-runnable Quick start as the validated operator entry path. (completed)
2) Keep the structure/invariants validation pass recorded as complete, without overclaiming artifact correctness. (completed)
3) Validate at least one retained bundle for artifact correctness, starting with the suspicious clip-timing case already observed in a selected bundle. (active)
4) Escalate to a cross-repo handoff only if the remaining artifact issue traces back to `vision_api` runtime metadata or clipping behavior rather than local bundle writing. (next)

### Verification
- Fast: `python3 -m compileall src`
- Targeted: `python3 -m pytest tests`
- Structure layer:
  - `python3 -m thermal_data_engine.cli --help`
  - `python3 -m thermal_data_engine.cli smoke-test --help`
  - `python3 -m thermal_data_engine.cli smoke-test --source "$SOURCE" --output-root "$OUT" --vision-api-url http://127.0.0.1:8000 --max-duration-sec 3.0`
  - `python3 -m thermal_data_engine.cli smoke-test --source "$SOURCE" --edge-config configs/edge/low_memory.yaml --output-root "$OUT" --vision-api-url http://127.0.0.1:8000 --use-edge-window`
  - `python3 -m thermal_data_engine.cli inspect recent --root "$OUT"`
- Artifact layer:
  - `ffprobe <bundle>/clip.mp4`
  - inspect one selected bundle's manifest and parquet outputs

### Risks / gotchas
- A lower-memory profile should stay inspectable and bounded, not become a vague collection of emergency flags.
- The fallback profile should not quietly erode the stable bundle contract or detector boundary.
- Smoke-test defaults intentionally provide their own bounded window unless `--use-edge-window` is passed, so operators must opt in when they specifically want to validate a named profile's own runtime window.
- Older Xavier-side virtualenvs may start with packaging tools too old for `pyproject.toml` editable installs; upgrade `pip`, `setuptools`, and `wheel` first.
- A retained bundle can be structurally present while still having suspicious media timing metadata, so inspect results must not be over-read.
- When `clip.mp4` is cut from `vision_api`'s already-bounded `runtime_input_path`, manifest timestamps are still absolute source timestamps. Bundle extraction must convert them back to runtime-relative offsets before calling ffmpeg.

### Decision rule for completion
- Treat the current repo slice as complete only when the structure/invariants layer is validated and the artifact-correctness layer is either validated on at least one retained bundle or converted into a concrete follow-up/handoff with clear acceptance language.

### Deferred work note
- Do not turn this task into model/backend redesign or cross-repo detector tuning unless artifact validation proves the issue cannot be handled from the thermal-data-engine side.
