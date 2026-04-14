## TASK_BRIEF

### Task
- Bootstrap and implement the initial Phase 1 edge capture + triage pipeline for `thermal-data-engine`, using `vision_api` as the detector service and producing structured clip bundles plus inspection utilities.

### Why this update
- The repo is still effectively greenfield. It currently contains design drafts, agent templates, and no runnable implementation.
- The broader Xavier NX bootstrap plan now needs a concrete edge-side data engine repo that can turn thermal video into downstream-friendly artifacts.

### Fixed invariants (do not change)
- Keep this repo edge-side only. Do not add training, CVAT, or desktop orchestration.
- Keep `vision_api` as the detector/runtime boundary instead of re-embedding DeepStream control logic here.
- Preserve stable bundle contracts: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`, with optional preview/debug artifacts.
- Prefer bounded offline file processing for the initial implementation, with clear extension points for longer-running service use.
- Keep Python 3.8-compatible syntax and typing where practical.

### Goal
- Deliver a runnable initial repo scaffold with config-driven offline ingestion, `vision_api` job submission + artifact consumption, simple tracking and clip selection, bundle writing, local upload abstraction, inspection tools, and focused tests/docs.

### Success criteria
- [x] Repo has its own initialized structure, repo-specific `AGENTS.md`, packaging metadata, config files, and task scratch files.
- [x] A file-based pipeline can submit work to local `vision_api`, consume `detections.jsonl`, assign track IDs, summarize tracks, and decide whether to keep a clip.
- [x] Saved bundles follow the Phase 1 contract and include manifest + parquet artifacts.
- [x] Inspection utilities can summarize recent clips, ambiguous clips, detector behavior, model version, and edge status from local artifacts.
- [x] Focused tests cover schemas/serialization, tracking or summarization logic, selection policy, and bundle validity.
- [~] Basic run documentation exists and the implementation passes meaningful local verification. Unit validation passed locally; end-to-end processing remains blocked until local `vision_api` is running.

### Relevant files (why)
- `Design_draft.md` — repo mission, scope boundaries, file layout, required outputs, and verification expectations.
- `TASK_BRIEF_draft.md` — concrete Phase 1 module list and expected interfaces.
- `docs/agent/TASK_BRIEF_TEMPLATE.md` — repo-local task brief convention.
- `docs/agent/MEMORY_TEMPLATE.md` — repo-local scratch memory convention.
- `../vision_api/AGENTS.md` — runtime constraints, branch workflow, and narrow-tool philosophy to preserve at the integration boundary.
- `../vision_api/app/main.py` — current local API surface for health and job submission.
- `../vision_api/app/schemas.py` — request contract for `yolo-inference` job submission.
- `../vision_api/app/runner.py` — shape of `detections.jsonl` and artifact outputs consumed here.
- `../vision_api/app/settings.py` — workspace roots and output directories that thermal-data-engine should respect.

### Refined Phase 2 Plan
1) Instantiate the repo skeleton: `AGENTS.md`, package layout, configs, docs, dependency metadata, and CLI entrypoints.
2) Implement shared schemas/config parsing plus a small `vision_api` client for local job submission and status polling.
3) Implement the core edge pipeline: structured detection loading, simple IoU-based tracking, track summarization, clip policy, bundle writing, and local upload abstraction.
4) Implement inspection utilities over saved bundles and run records.
5) Add focused tests and run fast verification passes.

### Small change sets (execution order)
1) Repo bootstrap + docs: `AGENTS.md`, `README.md`, `pyproject.toml`, `.gitignore`, package directories, default config files.
2) Shared models + config + `vision_api` integration: `src/thermal_data_engine/common/*`, `src/thermal_data_engine/vision_api/*`.
3) Edge pipeline core: `src/thermal_data_engine/edge/*`.
4) Agent/inspection tools + CLI wrappers: `src/thermal_data_engine/agent_tools/*`, `src/thermal_data_engine/cli.py`.
5) Tests + verification docs updates.

### Verification
- Fast: `python3 -m compileall src` ✅
- Targeted: `python3 -m pytest tests` ✅ (7 passed, 1 skipped because `pyarrow` is not installed)
- CLI smoke: `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect edge-status --root ~/.openclaw/workspace/outputs/thermal_data_engine` ✅
- Full: `python3 -m thermal_data_engine.cli process-file --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000` blocked for now because `vision_api` is not listening on `127.0.0.1:8000`.

### Risks / gotchas
- `vision_api` may not be running locally during validation, so the client and tests need graceful error handling and seams for fakes.
- `vision_api` currently emits detections but not persistent track IDs, so this repo needs a simple local tracker for Phase 1.
- Parquet writing may require optional runtime dependencies; keep errors explicit and tests focused.
- The repo is new, so defaults should stay conservative and inspectable rather than over-optimized.

### Decision rule for defaults
- Prefer the narrowest working default that preserves stable artifacts and can be validated locally. Defer richer realtime/service behavior unless the initial offline pipeline proves insufficient.

### Deferred work note
- Realtime stream ingestion, stronger MOT algorithms, remote upload backends, debug overlays, systemd units, and true OpenClaw runtime wiring may be scaffolded lightly but should not block the first runnable offline implementation.
