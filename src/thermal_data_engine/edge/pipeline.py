import hashlib
from pathlib import Path
from typing import Any, Dict, List

from thermal_data_engine.common.config import load_edge_config, load_policy_config
from thermal_data_engine.common.io import DATASETS_ROOT, ensure_dir, expand_path, path_relative_to_root, read_jsonl, utc_now_iso, write_json
from thermal_data_engine.common.models import BundleManifest, EdgeConfig
from thermal_data_engine.edge.bundle import write_bundle
from thermal_data_engine.edge.detections import flatten_detection_records
from thermal_data_engine.edge.policy import select_clip
from thermal_data_engine.edge.summarizer import summarize_tracks
from thermal_data_engine.edge.tracking import assign_track_ids
from thermal_data_engine.edge.upload import upload_bundle
from thermal_data_engine.vision_api.client import VisionApiClient


def _clip_id_for_source(source_path: Path) -> str:
    digest = hashlib.sha1(str(source_path).encode("utf-8")).hexdigest()[:12]
    return "clip-{}".format(digest)


def _run_id(clip_id: str) -> str:
    return "{}-{}".format(clip_id, utc_now_iso().replace(":", "").replace("-", ""))


def _vision_input_path(source_path: Path) -> str:
    if not source_path.exists():
        raise FileNotFoundError("SOURCE_NOT_FOUND: {}".format(str(source_path)))
    return path_relative_to_root(source_path, DATASETS_ROOT).replace("\\", "/")


def _build_job_payload(config: EdgeConfig, source_path: Path) -> Dict[str, Any]:
    vision = config.vision_request
    return {
        "job_label": "{}_{}".format(vision.job_label_prefix, source_path.stem),
        "input": {"kind": "video_file", "path": _vision_input_path(source_path)},
        "model_profile": vision.model_profile,
        "output_mode": vision.output_mode,
        "confidence_threshold": vision.confidence_threshold,
        "frame_stride": vision.frame_stride,
        "max_frames": vision.max_frames,
        "start_time_sec": vision.start_time_sec,
        "dataset_burst_gap_frames": vision.dataset_burst_gap_frames,
        "generate_preview_video": vision.generate_preview_video,
        "overwrite": vision.overwrite,
    }


def _resolve_frame_window(frame_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not frame_rows:
        return {"fps": None, "frame_count": 0, "width": 0, "height": 0, "start_ts": None, "end_ts": None}
    first_row = frame_rows[0]
    last_row = frame_rows[-1]
    return {
        "fps": None,
        "frame_count": len(frame_rows),
        "width": int(first_row.get("image_width", 0)),
        "height": int(first_row.get("image_height", 0)),
        "start_ts": None if first_row.get("source_timestamp_sec") is None else str(first_row.get("source_timestamp_sec")),
        "end_ts": None if last_row.get("source_timestamp_sec") is None else str(last_row.get("source_timestamp_sec")),
    }


def process_file(
    source: str,
    edge_config_path: str,
    policy_config_path: str,
    output_root_override: str = "",
    vision_api_url_override: str = "",
) -> Dict[str, Any]:
    edge_overrides = {}
    if output_root_override:
        edge_overrides["output_root"] = output_root_override
    if vision_api_url_override:
        edge_overrides["vision_api_url"] = vision_api_url_override

    edge_config = load_edge_config(edge_config_path, overrides=edge_overrides)
    policy_config = load_policy_config(policy_config_path)

    source_path = expand_path(source)
    output_root = expand_path(edge_config.output_root)
    bundle_root = ensure_dir(output_root / edge_config.bundle_subdir)
    run_root = ensure_dir(output_root / edge_config.run_subdir)
    upload_root = ensure_dir(output_root / edge_config.upload_subdir)

    clip_id = _clip_id_for_source(source_path)
    run_id = _run_id(clip_id)
    run_dir = ensure_dir(run_root / run_id)

    client = VisionApiClient(edge_config.vision_api_url)
    job_payload = _build_job_payload(edge_config, source_path)
    accepted = client.submit_yolo_job(job_payload)
    result = client.wait_for_job(
        accepted["job_id"],
        poll_interval_sec=edge_config.poll_interval_sec,
        timeout_sec=edge_config.poll_timeout_sec,
    )

    frame_rows = read_jsonl(result.detections_path)
    detections = flatten_detection_records(frame_rows, clip_id=clip_id)
    tracked = assign_track_ids(detections, edge_config.tracking)
    track_summaries = summarize_tracks(tracked, policy_config)
    selected, selection_reason, updated_tracks = select_clip(track_summaries, policy_config, frame_count=len(frame_rows))

    job_manifest = client.load_job_manifest(result)
    frame_window = _resolve_frame_window(frame_rows)
    detections_summary = job_manifest.get("detections_summary") or {}
    frame_window["fps"] = detections_summary.get("fps", frame_window["fps"])
    bundle_dir = bundle_root / clip_id
    runtime_input_path = Path(job_manifest.get("runtime_input_path") or source_path)
    manifest = BundleManifest(
        clip_id=clip_id,
        source_device_id=edge_config.device_id,
        source_path=str(source_path),
        start_ts=frame_window["start_ts"],
        end_ts=frame_window["end_ts"],
        fps=frame_window["fps"],
        frame_count=frame_window["frame_count"],
        width=frame_window["width"],
        height=frame_window["height"],
        model_version=edge_config.vision_request.model_profile,
        tracker_type="iou_greedy_v1",
        storage_uri=str(bundle_dir),
        created_at=utc_now_iso(),
        selection_reason=selection_reason,
        selected=selected,
        vision_job_id=result.job_id,
        run_id=run_id,
        track_count=len(updated_tracks),
        detection_count=len(tracked),
        extra={"vision_job_manifest": job_manifest},
    )

    write_json(run_dir / "vision_job_accepted.json", accepted)
    write_json(run_dir / "vision_job_status.json", result.status_payload)
    write_json(run_dir / "vision_job_manifest.json", job_manifest)

    upload_record = {
        "status": "skipped",
        "uri": "",
        "backend": edge_config.upload.backend,
    }
    bundle_record = {
        "status": "not_written",
        "clip_write_mode": None,
    }
    if selected:
        bundle_paths = write_bundle(
            bundle_dir=bundle_dir,
            source_clip_path=runtime_input_path,
            manifest=manifest,
            detections=tracked,
            tracks=updated_tracks,
        )
        bundle_record = {
            "status": "written",
            "bundle_dir": str(bundle_dir),
            "clip_write_mode": bundle_paths.get("clip_write_mode"),
        }
        upload_record = upload_bundle(
            bundle_dir=bundle_dir,
            upload_root=upload_root,
            config=edge_config.upload,
            clip_id=clip_id,
        )

    write_json(run_dir / "upload_record.json", upload_record)
    write_json(
        run_dir / "pipeline_summary.json",
        {
            "clip_id": clip_id,
            "run_id": run_id,
            "selected": selected,
            "selection_reason": selection_reason,
            "vision_job_id": result.job_id,
            "bundle_dir": str(bundle_dir),
            "source_path": str(source_path),
            "model_version": edge_config.vision_request.model_profile,
            "frame_window": frame_window,
            "frame_count": len(frame_rows),
            "detection_count": len(tracked),
            "track_count": len(updated_tracks),
            "job_detection_summary": detections_summary,
            "bundle": bundle_record,
            "upload": upload_record,
        },
    )

    return {
        "clip_id": clip_id,
        "run_id": run_id,
        "selected": selected,
        "selection_reason": selection_reason,
        "bundle_dir": str(bundle_dir),
        "vision_job_id": result.job_id,
        "upload": upload_record,
    }
