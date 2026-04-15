# thermal-data-engine

`thermal-data-engine` is the edge-side thermal video triage pipeline for OpenClaw. Phase 1 provides a runnable offline file-processing path that:

- submits a local detection job to `vision_api`
- loads structured detections from `detections.jsonl`
- assigns simple IoU-based track IDs
- summarizes tracks and applies a conservative clip-retention policy
- writes a stable clip bundle contract
- exposes local inspection helpers over saved artifacts

## Scope

Included in this repo:

- edge-side ingestion and triage
- tracking and track summaries
- clip bundle packaging
- local upload abstraction
- inspectable local diagnostics

Explicitly excluded:

- model training
- annotation or CVAT workflows
- desktop orchestration
- DeepStream control logic already owned by `vision_api`

## Install

```bash
python3 -m pip install -e .[dev]
```

Parquet bundle output requires a backend such as `pyarrow`. The pipeline raises an explicit error if no parquet backend is available.

For the first real runs on the NX, the defaults avoid preview-video rendering because it adds extra memory pressure during detector bring-up.

## Configs

- `configs/edge/default.yaml` defines the detector request, polling behavior, output roots, and upload defaults.
  - The default runtime request is intentionally conservative for NX bring-up: `dataset_package` output with preview disabled and `max_frames: 600`.
- `configs/data/clip_policy.yaml` defines the initial clip selection thresholds.

You can override either with CLI flags.

## Run

Start `vision_api` separately, then process a file:

```bash
python3 -m thermal_data_engine.cli process-file \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000
```

Inspect saved bundles:

```bash
python3 -m thermal_data_engine.cli inspect recent --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect ambiguous --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect detector --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect clip-artifacts --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect edge-status --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect runs --root ~/.openclaw/workspace/outputs/thermal_data_engine
```

## Output layout

Run records:

```text
<output_root>/runs/<run_id>/
```

Each run directory includes a `pipeline_summary.json`, so non-selected runs remain inspectable even when no bundle is retained. The summary now carries frame-window metadata, detection and track counts, plus upload status for quick troubleshooting and local handoff checks. `inspect edge-status` now also rolls up recent upload outcomes, so operators can quickly see whether recent runs were uploaded, skipped, or failed.

Saved clip bundles:

```text
<output_root>/bundles/<clip_id>/
├─ clip.mp4
├─ detections.parquet
├─ tracks.parquet
└─ clip_manifest.json
```

When a run has a bounded `start_ts` and `end_ts`, bundle writing now tries to cut `clip.mp4` down to that observed time window with `ffmpeg`. If segment extraction is unavailable or fails, it falls back to copying the runtime input so the stable bundle contract still holds.

Bundle manifests now record `extra.clip_artifact.write_mode`, and `inspect clip-artifacts` summarizes how often bundles were written by segment extraction versus source-copy fallback.

Optional local upload copies:

```text
<output_root>/uploads/local/<clip_id>/
```

## Validation

```bash
python3 -m compileall src
python3 -m pytest tests
```
