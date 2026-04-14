# TASK BRIEF — Phase 1: Edge Capture + Triage (Xavier NX + OpenClaw)

## Objective

Implement the **edge-side data generation and triage pipeline** on the Xavier NX using YOLO11m + tracking, integrated with OpenClaw.

This phase produces:

* Structured clip bundles
* Track-level metadata
* Uploadable artifacts for desktop curation
* Basic OpenClaw tools for inspection

No training or annotation workflows are included in this phase.

---

## Success Criteria

The system is considered complete when:

1. NX continuously processes video input (file or stream)
2. YOLO11m detection + tracking runs reliably
3. Clip bundles are generated with:

   * video
   * detections
   * track summaries
   * metadata
4. Only **selected clips** are persisted/uploaded
5. OpenClaw exposes tools to:

   * inspect recent clips
   * inspect ambiguous clips
   * summarize detector behavior
6. System runs as a stable service (systemd)

---

## Scope

### Included

* Detection + tracking pipeline
* Clip segmentation + writing
* Track summarization
* Clip selection policy
* Bundle packaging
* Local storage + upload interface
* OpenClaw tools (read-only + triage)

### Excluded

* Training
* Dataset curation
* CVAT integration
* Trust scoring beyond simple heuristics
* Model improvement loop

---

## Key Design Principle

The edge system **does not decide truth**.

It produces:

* high-confidence signals
* ambiguous candidates
* structured metadata

The desktop system will decide:

* what is labeled
* what is trained on

---

## Dependencies

* Ultralytics YOLO11 (Python API or CLI)
* PyTorch (Jetson-compatible)
* OpenCV
* ffmpeg
* Parquet (pyarrow)
* OpenClaw agent runtime
* systemd

YOLO supports detection and tracking modes via CLI or Python, including multi-object tracking with BoT-SORT or ByteTrack ([Ultralytics Docs][1])

---

## Implementation Plan

## 1. Detection + Tracking Module

File:

```
src/edge/detect_track.py
```

Responsibilities:

* Load YOLO11m model
* Run inference on video stream or file
* Run tracking (ByteTrack or BoT-SORT)

Required output per frame:

* frame_idx
* bbox (xyxy)
* confidence
* class_id
* track_id

Example (Python-style):

```python
from ultralytics import YOLO

model = YOLO("yolo11m.pt")

results = model.track(
    source=video_path,
    tracker="bytetrack.yaml",
    persist=True
)
```

Tracking assigns persistent IDs across frames, enabling multi-object tracking ([Ultralytics Docs][1])

---

## 2. Clip Writer

File:

```
src/edge/clip_writer.py
```

Responsibilities:

* Segment stream into clips (5–20 seconds)
* Maintain rolling buffer
* Save clip when triggered by policy

Output:

```
bundle/
├─ clip.mp4
├─ detections.parquet
├─ tracks.parquet
├─ clip_manifest.json
├─ preview.jpg
└─ debug_overlay.mp4 (optional)
```

---

## 3. Track Summarizer

File:

```
src/edge/summarizer.py
```

Compute per-track metrics:

* duration_frames
* mean_conf
* min_conf
* bbox_area_mean
* bbox_jitter (frame-to-frame IoU)
* edge_fraction
* detection_density

Output:

```
tracks.parquet
```

---

## 4. Clip Selection Policy

File:

```
configs/data/clip_policy.yaml
```

Initial simple rules:

### Save clip if ANY:

* track duration > T_min AND mean_conf > C_high
* track jitter > J_threshold (unstable)
* zero detections BUT motion/entropy heuristic high

### Drop clip if:

* no detections AND low motion
* extremely short duration

Keep policy simple — refine later.

---

## 5. Bundle Packaging

File:

```
src/edge/io.py
```

Responsibilities:

* Serialize detections → Parquet
* Serialize tracks → Parquet
* Write manifest JSON

Manifest fields:

* clip_id
* device_id
* timestamps
* model_version
* tracker_type
* frame_count
* resolution

---

## 6. Upload Module

File:

```
src/edge/upload.py
```

Responsibilities:

* Upload bundles to desktop storage
* Support:

  * local disk (dev)
  * S3 / network share (prod)

Interface:

```python
upload_bundle(bundle_path)
```

---

## 7. OpenClaw Agent Tools

Directory:

```
src/agent_tools/
```

### Tool 1 — recent_clips

```python
recent_clips(limit=20, filter=None)
```

Returns:

* clip_id
* timestamp
* detection count
* mean confidence

---

### Tool 2 — ambiguous_clips

```python
ambiguous_clips(limit=20)
```

Criteria:

* low mean_conf OR high jitter

---

### Tool 3 — detector_summary

```python
detector_summary(window="1h")
```

Returns:

* # clips processed
* # clips saved
* avg detections per clip
* confidence histogram

---

### Tool 4 — model_version

```python
model_version()
```

Returns:

* model file
* version tag
* load timestamp

---

### Tool 5 — edge_status

```python
edge_status()
```

Returns:

* GPU usage
* memory
* disk usage
* queue size

---

## 8. Service Runner

File:

```
src/edge/ingest.py
```

Responsibilities:

* main loop
* connect pipeline:

  * ingest → detect → summarize → select → write → upload

CLI:

```bash
python -m src.edge.ingest --source <video_or_stream>
```

---

## 9. Systemd Service

File:

```
scripts/edge_run.sh
```

Systemd unit:

```
/etc/systemd/system/edge-yolo.service
```

Requirements:

* auto-restart
* logs to journald
* configurable source

---

## 10. Config Files

```
configs/edge/inference.yaml
configs/edge/tracker.yaml
configs/data/clip_policy.yaml
```

Keep configs external — no hardcoding.

---

## Deliverables

### Code

* edge pipeline modules
* agent tools
* configs
* service runner

### Artifacts

* sample clip bundles
* logs
* OpenClaw tool outputs

---

## Non-Goals (Important)

Do NOT:

* implement training
* integrate CVAT
* build dataset splits
* optimize pseudo-label trust deeply
* tune model performance

This phase is **data generation only**.

---

## Risks

* NX performance bottlenecks
* tracker instability under ego motion
* disk fill from excessive clip saving
* poor clip selection thresholds

Mitigation:

* conservative clip policy
* logging + metrics
* adjustable configs

---

## Definition of Done

* NX runs continuously without crashing
* Clip bundles are valid and structured
* OpenClaw tools return correct outputs
* Desktop can ingest bundles without modification

---

## Next Phase (Not part of this task)

* Trust scoring
* Review queue generation
* CVAT annotation loop
* Student training pipeline

---

## Summary

This phase builds the **data engine**.

It transforms raw thermal video into:

* structured clips
* track-aware metadata
* prioritized samples

This is the foundation for the entire bootstrap learning system.

[1]: https://docs.ultralytics.com/modes/track/?utm_source=chatgpt.com "Multi-Object Tracking with Ultralytics YOLO"
