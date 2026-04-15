## TASK_BRIEF

### Task
- Add a lower-memory or fallback runtime profile to `thermal-data-engine` so constrained Xavier NX bring-up has a safer bounded path when the default edge settings still hit memory pressure.

### Why this update
- The new smoke-test workflow is in place and validated, so the next edge-side refinement is reducing bring-up fragility under tighter NX memory conditions.
- Earlier real runs already exposed memory pressure (`Couldn't create nvvic Session: Cannot allocate memory`) when the runtime request was heavier than the device liked. A named lower-memory profile is the cleanest next incremental hedge.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary instead of re-embedding DeepStream control logic here.
- Preserve stable bundle contracts: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer bounded, inspectable validation flows over hidden background behavior.

### Goal
- Provide an explicit lower-memory runtime path that operators and scheduled work can choose when the default profile is too heavy, without changing the stable edge-side API contract.

### Success criteria
- [x] A named lower-memory or fallback edge config/profile exists.
- [x] The profile is documented clearly enough that operators know when to use it.
- [x] The smoke-test or bounded validation path can exercise the lower-memory profile.
- [x] Focused verification covers the new profile and its intended use.

### Relevant files (why)
- `configs/edge/default.yaml` — current conservative baseline
- `configs/edge/` — likely home for a lower-memory profile variant
- `src/thermal_data_engine/cli.py` — smoke-test and process-file entrypoints that should be able to use the profile cleanly
- `README.md` — operator-facing profile guidance
- `tests/` — focused regression or config coverage

### Refined Phase 2 Plan
1) Inspect which knobs are most likely to reduce memory pressure without breaking the stable contract.
2) Add a named lower-memory profile and wire any minimal CLI support needed to exercise it.
3) Update docs and run a bounded validation that proves the profile works as intended. (completed with targeted config/smoke tests)

### Small change sets (execution order)
1) Profile/config changes under `configs/edge/`.
2) Minimal CLI or helper adjustments only if the profile is awkward to use otherwise.
3) Docs and validation updates.

### Verification
- Fast: `python3 -m compileall src`
- Targeted: `python3 -m pytest tests`
- Full: run the smoke-test or a bounded process-file command against a local sample using the lower-memory profile.

### Risks / gotchas
- A lower-memory profile should stay inspectable and bounded, not become a vague collection of emergency flags.
- The fallback profile should not quietly erode the stable bundle contract or detector boundary.
- Smoke-test defaults still intentionally provide their own bounded window unless `--use-edge-window` is passed, so operators must opt in when they specifically want to validate a named profile's own runtime window.

### Decision rule for defaults
- Keep the existing default profile as the normal path unless the lower-memory variant proves materially safer with acceptable validation quality.

### Deferred work note
- Do not turn this task into model/backend redesign or cross-repo detector tuning unless validation proves the issue cannot be handled from the thermal-data-engine side.
