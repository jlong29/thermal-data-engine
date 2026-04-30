# AGENTS.md — Companion Guide for Phase 1 Edge Capture + Triage

## Purpose

This document defines the scope and design of the **thermal-data-engine** repo in src/thermal-data-engine. The first task is to translate this design into an init implementation of this repo.

This repo is building the **edge-side data engine**, not the full learning loop. The goal for this repo is to provide a set of tools for transforming raw thermal video into structured clip bundles and expose basic OpenClaw inspection tools.

The agent must optimize for:

* correctness
* stable service behavior
* clean repo organization
* incremental verification
* minimal scope creep

**NOTE**: This repo should use the tools provided in the src/vision_api repo. Its work must keep the vision_api in mind.

---

## Scope Discipline

This phase includes only:

* edge inference
* multi-object tracking
* clip extraction
* metadata packaging
* upload interface
* OpenClaw inspection tools
* service wiring

This phase does **not** include:

* model training
* pseudo-label trust research beyond simple heuristics
* annotation pipelines
* CVAT integration
* dataset curation UI
* student/teacher training loop
* active learning
* desktop orchestration

If a possible improvement belongs to a later phase, note it briefly and move on.

---

## Primary Objective

Implement a working edge-side pipeline that:

* runs YOLO11m on the Xavier NX
* performs tracking
* writes clip bundles
* selects clips using simple heuristics
* exposes useful OpenClaw tools
* can run continuously as a service

Success is defined by operational reliability and clean handoff of edge artifacts to the desktop workflow.

**NOTE**: The src/vision_api provides tools for running the YOLO11m model on the Xavier NX via DeepStream

---

## Repo Behavior Rules

### 1. Favor small, testable changes

Do not attempt a large one-shot rewrite. Land the system in small verified steps.

### 2. Prefer explicit over clever

Avoid overly abstract designs. Keep modules boring and inspectable.

### 3. Keep configs external

Thresholds, tracker settings, source definitions, and output paths belong in config files, not hardcoded logic.

### 4. Build around structured artifacts

Every edge output should be machine-readable and easy for downstream tools to consume.

### 5. Preserve future desktop compatibility

Phase 1 outputs must be shaped so later curation and training stages can consume them without redesign.

---

## Required Repo Understanding

Before changing code, inspect and summarize:

* current repo structure
* current OpenClaw integration points
* current YOLO integration points
* deployment/runtime environment on the NX
* existing service scripts
* existing config conventions
* logging conventions
* any current artifact or manifest conventions

Do not assume these are absent. Verify. Look at src/vision_api

---

## Implementation Priorities

Implement in this order unless repo reality strongly suggests otherwise.

### Priority 1 — Core schemas and artifact format

Create or normalize the data structures for:

* clip manifest
* detection records
* track summaries

These formats must be stable before higher-level tools are built.

If it makes sense to refactor src/vision_api such that these live here, then do it. We want the vision_api to be responsible for running the model efficiently and this repo to exercise these tools.

### Priority 2 — Detection + tracking pipeline

Implement the edge inference module that runs YOLO11m with tracking and emits per-frame detections plus track IDs.

**NOTE**: the vision_api already provides a lot of these tools, though not the movie-specific tracking tools.

### Priority 3 — Clip writing

Implement clip segmentation and bundle writing.

**NOTE**: example videos may be found at ~/.openclawInfo/datasets/incoming. Use these videos for testing.

### Priority 4 — Selection policy

Implement simple rule-based clip retention.

### Priority 5 — Upload interface

Implement a clean upload abstraction, even if the first version only supports local or mocked upload. The roadmap has this edge device uploading video clips to a storage point monitored by the compute node for fine tuning the YOLO11 model.

### Priority 6 — OpenClaw tools

Expose inspection and summary tools against local edge artifacts.

### Priority 7 — Service integration

Wire the pipeline into a runnable entrypoint and service form.

---

## FileSystem Design

Use these areas unless evidence suggests better options:

```text
src/common/        shared schemas, io helpers, manifest logic
src/edge/          ingest, detect, track, summarize, write, upload
src/agent_tools/   OpenClaw-facing utilities
configs/edge/      runtime configs
configs/data/      clip policy
scripts/           runner scripts
tests/             focused unit tests
docs/              architecture and operating notes
```

---

## Coding Rules

### General

* Use clear names.
* Avoid hidden side effects.
* Validate external inputs.
* Fail with useful logs.
* Keep serialization deterministic.

### Python

* Add type hints where practical.
* Keep functions small.
* Separate pure logic from side-effecting IO.
* Avoid global mutable state unless clearly necessary for service lifecycle.

### Logging

* Log state transitions and failure points.
* Do not spam logs per frame unless debug mode is enabled.
* Make logs useful for edge debugging.

### Config handling

* Load configs once, validate them early, and pass structured config objects through the pipeline.

---

## Data Contract Requirements

The edge pipeline must produce structured artifacts suitable for downstream curation.

### Minimum bundle contents

Each saved clip bundle should contain:

* `clip.mp4`
* `detections.parquet`
* `tracks.parquet`
* `clip_manifest.json`

Optional:

* `preview.jpg`
* `debug_overlay.mp4`

### Minimum manifest fields

* clip_id
* source_device_id
* start_ts
* end_ts
* fps
* frame_count
* width
* height
* model_version
* tracker_type
* storage path or URI
* creation timestamp

### Detection fields

* clip_id
* frame_idx
* track_id
* class_id
* confidence
* bbox coordinates

### Track summary fields

* clip_id
* track_id
* duration_frames
* mean_conf
* min_conf
* bbox_area_mean
* bbox_jitter
* edge_fraction
* selection_reason

Do not postpone these definitions.

---

## OpenClaw Tool Requirements

The first tools should be operationally useful and simple.

### Must-have tools

* `recent_clips`
* `ambiguous_clips`
* `detector_summary`
* `model_version`
* `edge_status`

### Expectations

Each tool should:

* read from local artifacts or service state
* return structured data
* degrade gracefully if no data is present
* avoid blocking the main inference loop

---

## Verification Rules

Every meaningful change must be followed by verification.

### Verify at three levels

#### 1. Unit level

Schemas, summarization logic, and policy logic should have basic tests.

#### 2. Module level

Run the detector/tracker on a short sample and verify output files are valid.

#### 3. Service level

Run the end-to-end pipeline locally on a short input and verify:

* clips are saved correctly
* manifests are valid
* tools can read results

### Minimum required checks

* output bundle structure exists
* parquet files open successfully
* manifest keys are present
* tracker IDs are propagated
* clip policy gates output as expected

---

## Performance Rules

This is an edge system. Respect constraints.

* Do not assume desktop-class resources.
* Avoid keeping unnecessary full-resolution data in memory.
* Prefer streaming or bounded buffering.
* Make clip retention conservative by default.
* Do not enable expensive debug artifacts by default.

If there is a performance tradeoff, prefer stability over completeness.

---

## Failure Handling

Handle these gracefully:

* model load failure
* invalid input source
* ffmpeg or video writer failure
* upload failure
* empty detections
* malformed config
* low disk space

For recoverable failures:

* log clearly
* skip or back off
* continue if safe

For unrecoverable failures:

* fail fast and visibly

---

## Testing Philosophy

Do not overbuild test infrastructure for Phase 1, but do include enough coverage to prevent regressions.

Recommended tests:

* schema serialization test
* track summary calculation test
* clip policy selection test
* bundle roundtrip validity test

**NOTE**: this is what the videos at ~/.openclawInfo/datasets/incoming can be used for

---

## Documentation Rules

When the implementation stabilizes, document:

* how to run the pipeline
* config meanings
* expected outputs
* OpenClaw tool behavior
* known limitations

Keep docs close to the implementation and update them as the code changes.

---

## Change Management

When editing existing code:

* preserve behavior unless the task requires change
* avoid incidental refactors
* do not rename broad swaths of the repo without need
* keep diffs reviewable

When creating new code:

* place it where future phases will naturally find it
* keep interfaces stable
* leave clear extension points without prematurely generalizing

---

## Decision Heuristics

When there is ambiguity, prefer:

* simpler module boundaries
* explicit file formats
* stable downstream contracts
* configs over code changes for thresholds
* service reliability over feature breadth
* clip quality over clip quantity

---

## Definition of Done for This Phase

Phase 1 is done when:

* a runnable edge pipeline exists
* YOLO11m detection + tracking works on sample input
* clip bundles are emitted in the expected format
* clip retention policy works
* OpenClaw tools can inspect local results
* the system can be run repeatedly without manual repair
* basic docs and tests exist

---

## Out-of-Scope Notes for Future Phases

Future phases may add:

* trust scoring refinement
* hard-case mining
* CVAT export/import
* gold eval set management
* student training
* TensorRT promotion workflow

These should be noted only when current design decisions affect future compatibility.

---

## Final Instruction

Do not optimize for theoretical elegance.

Optimize for a **working, inspectable, edge-safe data engine** that produces clean artifacts for the desktop-side bootstrap learning pipeline.
