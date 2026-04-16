# thermal-data-engine

`thermal-data-engine` is the edge-side thermal video triage pipeline for OpenClaw. Phase 1 provides a runnable offline file-processing path that:

- submits a local detection job to `vision_api`
- loads structured detections from `detections.jsonl`
- assigns simple IoU-based track IDs
- summarizes tracks and applies a conservative clip-retention policy
- writes a stable clip bundle contract
- exposes local inspection helpers over saved artifacts

## Quick start

If you want the shortest path from a fresh shell to a real smoke test, use two terminals.

### Terminal 1: start `vision_api`

```bash
cd /home/myclaw/.openclaw/workspace/src/vision_api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Optional health checks from another shell:

```bash
curl http://127.0.0.1:8000/v1/system/deepstream/status | python3 -m json.tool
curl http://127.0.0.1:8000/v1/system/gpu/status | python3 -m json.tool
```

### Terminal 2: install and run `thermal-data-engine`

```bash
cd /home/myclaw/.openclaw/workspace/src/thermal-data-engine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev,parquet]
python3 -m thermal_data_engine.cli smoke-test \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000 \
  --max-duration-sec 3.0
```

If you hit memory pressure during Xavier NX bring-up, retry with the lower-memory profile:

```bash
python3 -m thermal_data_engine.cli smoke-test \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --edge-config configs/edge/low_memory.yaml \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000 \
  --use-edge-window
```

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

Create and activate a local virtualenv first, then upgrade packaging tools and install the package in editable mode:

```bash
cd /home/myclaw/.openclaw/workspace/src/thermal-data-engine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
```

After that, the CLI should resolve in the active shell:

```bash
python3 -m thermal_data_engine.cli --help
# or
thermal-data-engine --help
```

Parquet bundle output requires a backend such as `pyarrow`. Install it in the same environment when you want real bundle writing:

```bash
python -m pip install -e .[dev,parquet]
```

The pipeline raises an explicit error if no parquet backend is available.

For the first real runs on the NX, the defaults avoid preview-video rendering because it adds extra memory pressure during detector bring-up.

## Configs

- `configs/edge/default.yaml` defines the detector request, polling behavior, output roots, and upload defaults.
  - The default runtime request is intentionally conservative for NX bring-up: `dataset_package` output with preview disabled and `max_frames: 600`.
  - When a source reports suspiciously high encoded fps metadata, the pipeline can automatically switch from a frame-count bound to a short duration bound so validation does not collapse into a fraction of a second.
- `configs/edge/low_memory.yaml` is the fallback Xavier NX bring-up profile.
  - Use it when the default profile still trips memory pressure or codec-session allocation issues.
  - It stays bounded by default with `max_frames: null`, `max_duration_sec: 3.0`, `frame_stride: 10`, and preview disabled.
- `configs/data/clip_policy.yaml` defines the initial clip selection thresholds.

You can override either with CLI flags.

## Run

### Start `vision_api`

`thermal-data-engine` expects the local `vision_api` FastAPI service to already be running.

In a separate shell:

```bash
cd /home/myclaw/.openclaw/workspace/src/vision_api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Optional preflight checks from another shell:

```bash
curl http://127.0.0.1:8000/v1/system/deepstream/status | python3 -m json.tool
curl http://127.0.0.1:8000/v1/system/gpu/status | python3 -m json.tool
```

For more `vision_api` details, see `../vision_api/README.md`.

### Run `thermal-data-engine`

With the `thermal-data-engine` virtualenv active, process a file:

```bash
python3 -m thermal_data_engine.cli process-file \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000
```

Process a whole folder of videos and assemble one training-facing Ultralytics package:

```bash
python3 -m thermal_data_engine.cli process-directory \
  --source-dir ~/.openclaw/workspace/datasets/incoming \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000 \
  --package-name incoming-sample
```

That command runs the normal per-file pipeline for each supported video in the folder, then combines the emitted per-job dataset packages into one handoff-ready package under `ultralytics_packages/<package_name>/`.

Run a fast bounded smoke test:

```bash
python3 -m thermal_data_engine.cli smoke-test \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000 \
  --max-duration-sec 3.0
```

Exercise the lower-memory profile directly during bring-up:

```bash
python3 -m thermal_data_engine.cli smoke-test \
  --source ~/.openclaw/workspace/datasets/incoming/example.mp4 \
  --edge-config configs/edge/low_memory.yaml \
  --output-root ~/.openclaw/workspace/outputs/thermal_data_engine \
  --vision-api-url http://127.0.0.1:8000 \
  --use-edge-window
```

Use `--use-edge-window` when you want the smoke test to keep the bounded runtime window from the selected edge profile instead of replacing it with the default smoke-test window.

Inspect saved bundles:

```bash
python3 -m thermal_data_engine.cli inspect recent --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect ambiguous --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect detector --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect clip-artifacts --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect edge-status --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect runs --root ~/.openclaw/workspace/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect ultralytics-package --path ~/.openclaw/workspace/outputs/inference_jobs/<job_id>/dataset
```

## Output layout

Run records:

```text
<output_root>/runs/<run_id>/
```

Each run directory includes a `pipeline_summary.json`, so non-selected runs remain inspectable even when no bundle is retained. The summary now carries run start/completion timestamps, frame-window metadata, detection and track counts, plus upload status for quick troubleshooting and local handoff checks. `inspect edge-status` now also rolls up recent upload outcomes, so operators can quickly see whether recent runs were uploaded, skipped, or failed.

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

Combined training-facing packages:

```text
<output_root>/ultralytics_packages/<package_id>/
├─ dataset.yaml
├─ images/
├─ labels/
├─ splits/
│  ├─ train.txt
│  └─ val.txt
└─ manifest.json
```

`manifest.json` records which source files and `vision_api` jobs contributed each packaged frame so the desktop fine-tuning machine gets one inspectable handoff root instead of a pile of per-job datasets.

For the staged thermal-owned packaging migration, `inspect ultralytics-package` validates the current training-facing package contract against the existing Ultralytics-style dataset layout. It checks for the expected `images/`, `labels/`, `splits/train.txt`, `splits/val.txt`, `dataset.yaml`, per-image label files, and normalized YOLO label rows so tomorrow's hotter-machine load/train smoke test has a concrete readiness check.

Optional local upload copies:

```text
<output_root>/uploads/local/<clip_id>/
```

## Validation

```bash
python3 -m compileall src
python3 -m pytest tests
```
