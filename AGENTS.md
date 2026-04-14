# AGENTS.md - thermal-data-engine

You are an AI coding agent operating inside the `thermal-data-engine` repository.

This file is always-on guidance. Keep it short, stable, and high-signal. If something is task-specific, it belongs in `.agent/TASK_BRIEF.md`, `.agent/MEMORY.md`, or other `.agent/` scratch artifacts, not here.

---

## Mission
`thermal-data-engine` is the edge-side thermal video capture and triage pipeline for OpenClaw.
It turns raw thermal video into structured clip bundles, track summaries, and lightweight inspection outputs while keeping `vision_api` as the detector/runtime boundary.
Phase 1 focuses on bounded offline file processing with conservative defaults that can later be extended into a longer-running edge service.

## Source of truth
When docs and code disagree, trust these files:
- `src/thermal_data_engine/cli.py` - CLI entrypoints and user-facing workflow
- `src/thermal_data_engine/edge/pipeline.py` - main offline processing path
- `src/thermal_data_engine/vision_api/client.py` - `vision_api` integration boundary
- `src/thermal_data_engine/common/models.py` - stable bundle and record schemas
- `src/thermal_data_engine/common/config.py` - config loading and defaults

Additional repo-specific rules:
- Keep this repo edge-side only; do not add training, CVAT, or desktop orchestration.
- Preserve `vision_api` as the detector/runtime boundary; do not copy its DeepStream control logic here.
- Preserve stable bundle contents: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer inspectable defaults and explicit artifacts over hidden background behavior.

---

## Repo map

### High-signal code
- `src/thermal_data_engine/` - main package
  - `common/` - schemas, config models, serialization, shared utilities
  - `vision_api/` - local HTTP client for job submission and polling
  - `edge/` - detection loading, tracking, summarization, policy, bundling, upload, pipeline
  - `agent_tools/` - local inspection helpers over saved artifacts
- `configs/` - default edge runtime and clip-policy configs
- `tests/` - focused unit tests
- `README.md` - repo overview and runnable commands

### Large/noisy dirs (do not scan by default)
Avoid expensive traversal unless explicitly needed:
- `.git/`
- `.venv/`
- `~/.openclaw/workspace/datasets/`
- `~/.openclaw/workspace/outputs/`
- `__pycache__/`

Use targeted commands and keep output small.

---

## Core workflow (minimal commands)

### Build / prepare
```bash
python3 -m pip install -e .[dev]
```

### Main run path
```bash
python3 -m thermal_data_engine.cli process-file \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine
```

### Secondary workflows
```bash
python3 -m thermal_data_engine.cli inspect recent --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect ambiguous --root ~/.openclaw/workspace/outputs/thermal_data_engine
```

### Validate
```bash
python3 -m compileall src
python3 -m pytest tests
```

Notes:
- `vision_api` must be running separately for end-to-end processing.
- Bundle writing requires an available parquet backend such as `pyarrow`.

---

## Metadata contracts (important)
- Inputs / outputs written to disk:
  - `configs/edge/*.yaml` and `configs/data/*.yaml` define runtime and policy defaults.
  - `<output_root>/runs/<run_id>/` stores pipeline run records and copied `vision_api` job metadata.
  - `<output_root>/bundles/<clip_id>/` stores `clip.mp4`, parquet artifacts, and `clip_manifest.json`.
  - `<output_root>/uploads/` stores local upload copies and upload records when enabled.
- Runtime invariants:
  - `vision_api` is called over HTTP and remains the detector boundary.
  - `detections.jsonl` is treated as the source detection artifact from `vision_api`.
  - Bundle schemas and manifest keys should stay backward compatible once emitted.

---

## Tests (default)
Run the fastest meaningful checks first:
```bash
python3 -m compileall src
python3 -m pytest tests
```

---

## Coding/style conventions
- Python 3.8 compatibility matters.
- Use explicit dataclasses and typed helper functions for inspectable behavior.
- Prefer localized diffs; avoid broad formatting-only changes.
- Keep IO separate from pure selection/tracking logic where practical.

