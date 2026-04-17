import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

from thermal_data_engine.common.config import load_edge_config, load_policy_config
from thermal_data_engine.common.io import DATASETS_ROOT, ensure_dir, expand_path, path_relative_to_root, probe_video_metadata, read_json, read_jsonl, utc_now_iso, write_json
from thermal_data_engine.common.models import BundleManifest, EdgeConfig
from thermal_data_engine.edge.bundle import write_bundle
from thermal_data_engine.edge.detections import flatten_detection_records
from thermal_data_engine.edge.policy import select_clip
from thermal_data_engine.edge.summarizer import summarize_tracks
from thermal_data_engine.edge.tracking import assign_track_ids
from thermal_data_engine.edge.upload import upload_bundle
from thermal_data_engine.vision_api.client import VisionApiClient


_VIDEO_SUFFIXES = (".mp4", ".mov", ".m4v", ".avi", ".mkv")


def _clip_id_for_source(source_path: Path) -> str:
    digest = hashlib.sha1(str(source_path).encode("utf-8")).hexdigest()[:12]
    return "clip-{}".format(digest)


def _run_id(clip_id: str) -> str:
    return "{}-{}".format(clip_id, utc_now_iso().replace(":", "").replace("-", ""))


def _vision_input_path(source_path: Path) -> str:
    if not source_path.exists():
        raise FileNotFoundError("SOURCE_NOT_FOUND: {}".format(str(source_path)))
    return path_relative_to_root(source_path, DATASETS_ROOT).replace("\\", "/")


def _resolve_windowing(config: EdgeConfig, source_path: Path) -> Dict[str, Any]:
    vision = config.vision_request
    payload_overrides = {
        "max_frames": vision.max_frames,
        "max_duration_sec": vision.max_duration_sec,
    }
    decision = {"mode": "configured", "reason": "direct_request", "source_probe": None}

    try:
        source_probe = probe_video_metadata(source_path)
    except Exception as exc:
        decision = {"mode": "configured", "reason": "probe_failed", "source_probe": None, "probe_error": str(exc)}
        return {"payload_overrides": payload_overrides, "decision": decision}

    decision["source_probe"] = source_probe
    fps = source_probe.get("fps")
    fallback_fps = vision.fallback_fps if vision.fallback_fps > 0 else None
    min_duration_sec = vision.min_duration_sec_on_suspicious_fps
    if vision.max_duration_sec is None and vision.max_frames is not None:
        if fps is None or fps <= 0:
            if fallback_fps is not None:
                derived_duration_sec = float(vision.max_frames) / float(fallback_fps)
                payload_overrides["max_frames"] = None
                payload_overrides["max_duration_sec"] = derived_duration_sec
                decision = {
                    "mode": "auto_duration_override",
                    "reason": "missing_fps_using_fallback",
                    "source_probe": source_probe,
                    "fallback_fps": fallback_fps,
                    "derived_duration_sec": derived_duration_sec,
                }
        elif fps >= vision.suspicious_fps_threshold and min_duration_sec > 0:
            implied_window_sec = float(vision.max_frames) / float(fps)
            payload_overrides["max_frames"] = None
            payload_overrides["max_duration_sec"] = min_duration_sec
            decision = {
                "mode": "auto_duration_override",
                "reason": "suspicious_high_fps",
                "source_probe": source_probe,
                "implied_window_sec": implied_window_sec,
                "min_duration_sec_on_suspicious_fps": min_duration_sec,
            }
        elif fallback_fps is not None and fps >= vision.fallback_fps_threshold:
            derived_duration_sec = float(vision.max_frames) / float(fallback_fps)
            payload_overrides["max_frames"] = None
            payload_overrides["max_duration_sec"] = derived_duration_sec
            decision = {
                "mode": "auto_duration_override",
                "reason": "high_fps_using_fallback",
                "source_probe": source_probe,
                "reported_fps": fps,
                "fallback_fps": fallback_fps,
                "fallback_fps_threshold": vision.fallback_fps_threshold,
                "derived_duration_sec": derived_duration_sec,
            }

    return {"payload_overrides": payload_overrides, "decision": decision}


def _build_job_payload(config: EdgeConfig, source_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    vision = config.vision_request
    windowing = _resolve_windowing(config, source_path)
    payload = {
        "job_label": "{}_{}".format(vision.job_label_prefix, source_path.stem),
        "input": {"kind": "video_file", "path": _vision_input_path(source_path)},
        "model_profile": vision.model_profile,
        "output_mode": vision.output_mode,
        "confidence_threshold": vision.confidence_threshold,
        "frame_stride": vision.frame_stride,
        "max_frames": windowing["payload_overrides"]["max_frames"],
        "max_duration_sec": windowing["payload_overrides"]["max_duration_sec"],
        "start_time_sec": vision.start_time_sec,
        "dataset_burst_gap_frames": vision.dataset_burst_gap_frames,
        "generate_preview_video": vision.generate_preview_video,
        "overwrite": vision.overwrite,
    }
    return payload, windowing


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


def _write_dataset_yaml(dataset_root: Path, class_name: str) -> None:
    yaml_text = "path: .\ntrain: splits/train.txt\nval: splits/val.txt\nnames:\n  0: {}\n".format(class_name)
    (dataset_root / "dataset.yaml").write_text(yaml_text)


def _list_video_sources(source_dir: Path) -> List[Path]:
    if not source_dir.exists() or not source_dir.is_dir():
        raise NotADirectoryError("SOURCE_DIR_NOT_FOUND: {}".format(str(source_dir)))
    sources = [
        path
        for path in sorted(source_dir.iterdir())
        if path.is_file() and path.suffix.lower() in _VIDEO_SUFFIXES
    ]
    if not sources:
        raise FileNotFoundError("NO_VIDEO_SOURCES_FOUND: {}".format(str(source_dir)))
    return sources


def _split_entries(dataset_root: Path, split_name: str) -> List[str]:
    split_path = dataset_root / "splits" / "{}.txt".format(split_name)
    if not split_path.exists():
        raise FileNotFoundError("DATASET_SPLIT_MISSING: {}".format(str(split_path)))
    return [line.strip() for line in split_path.read_text().splitlines() if line.strip()]


def _label_path_for_image(dataset_root: Path, image_rel_path: str) -> Path:
    image_rel = Path(image_rel_path)
    if image_rel.parts and image_rel.parts[0] == "images":
        image_rel = Path(*image_rel.parts[1:])
    return dataset_root / "labels" / image_rel.with_suffix(".txt")


def _copy_split_entry(dataset_root: Path, image_rel_path: str, destination_root: Path, file_prefix: str) -> str:
    source_image_path = dataset_root / image_rel_path
    if not source_image_path.exists():
        raise FileNotFoundError("DATASET_IMAGE_MISSING: {}".format(str(source_image_path)))

    source_label_path = _label_path_for_image(dataset_root, image_rel_path)
    if not source_label_path.exists():
        raise FileNotFoundError("DATASET_LABEL_MISSING: {}".format(str(source_label_path)))

    destination_name = "{}__{}".format(file_prefix, source_image_path.name)
    destination_image_rel = Path("images") / destination_name
    destination_label_rel = Path("labels") / Path(destination_name).with_suffix(".txt")
    destination_image_path = destination_root / destination_image_rel
    destination_label_path = destination_root / destination_label_rel

    if destination_image_path.exists() or destination_label_path.exists():
        raise RuntimeError("DATASET_ENTRY_COLLISION: {}".format(destination_name))

    destination_image_path.parent.mkdir(parents=True, exist_ok=True)
    destination_label_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image_path, destination_image_path)
    shutil.copy2(source_label_path, destination_label_path)
    return str(destination_image_rel).replace("\\", "/")


def _package_id_for_directory(source_dir: Path) -> str:
    return "{}-{}".format(source_dir.name, utc_now_iso().replace(":", "").replace("-", ""))


def _combine_source_datasets(package_root: Path, batch_id: str, source_dir: Path, source_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    ensure_dir(package_root / "images")
    ensure_dir(package_root / "labels")
    splits_dir = ensure_dir(package_root / "splits")

    combined_train = []
    combined_val = []
    combined_entries = []
    package_sources = []
    total_target_detections = 0
    total_frames_with_target_detections = 0
    class_name = "person"

    for index, item in enumerate(source_results, start=1):
        dataset_root = Path(item["dataset_root"])
        dataset_manifest = item["dataset_manifest"]
        class_map = dataset_manifest.get("class_map") or {"0": class_name}
        source_class_name = class_map.get("0") or dataset_manifest.get("target_class_name") or class_name
        if source_class_name != class_name:
            raise RuntimeError(
                "DATASET_CLASS_MISMATCH: expected {} but found {} in {}".format(
                    class_name, source_class_name, str(dataset_root)
                )
            )

        train_entries = _split_entries(dataset_root, "train")
        val_entries = _split_entries(dataset_root, "val")
        prefix = "{:02d}_{}".format(index, Path(item["source_path"]).stem)
        remapped_entries = {}

        for split_name, entries, destination in (
            ("train", train_entries, combined_train),
            ("val", val_entries, combined_val),
        ):
            for entry in entries:
                remapped = _copy_split_entry(dataset_root, entry, package_root, prefix)
                remapped_entries[entry] = {"image_path": remapped, "split": split_name}
                destination.append(remapped)

        dataset_entries = dataset_manifest.get("entries") or []
        for dataset_entry in dataset_entries:
            original_image_path = dataset_entry.get("image_path")
            remapped = remapped_entries.get(original_image_path)
            if remapped is None:
                continue
            combined_entries.append(
                {
                    "source_path": item["source_path"],
                    "source_clip_id": item["clip_id"],
                    "source_run_id": item["run_id"],
                    "source_vision_job_id": item["vision_job_id"],
                    "source_dataset_root": str(dataset_root),
                    "source_image_path": original_image_path,
                    "source_label_path": dataset_entry.get("label_path"),
                    "image_path": remapped["image_path"],
                    "label_path": remapped["image_path"].replace("images/", "labels/").rsplit(".", 1)[0] + ".txt",
                    "split": remapped["split"],
                    "frame_num": dataset_entry.get("frame_num"),
                    "timestamp_sec": dataset_entry.get("timestamp_sec"),
                    "source_timestamp_sec": dataset_entry.get("source_timestamp_sec"),
                    "target_detection_count": dataset_entry.get("target_detection_count", 0),
                }
            )

        total_target_detections += int(dataset_manifest.get("total_target_detections", 0))
        total_frames_with_target_detections += int(dataset_manifest.get("frames_with_target_detections", 0))
        package_sources.append(
            {
                "source_path": item["source_path"],
                "clip_id": item["clip_id"],
                "run_id": item["run_id"],
                "vision_job_id": item["vision_job_id"],
                "selected": item["selected"],
                "selection_reason": item["selection_reason"],
                "dataset_root": str(dataset_root),
                "dataset_manifest_path": item["dataset_manifest_path"],
                "image_count": int(dataset_manifest.get("image_count", 0)),
                "label_count": int(dataset_manifest.get("label_count", 0)),
                "train_image_count": int(dataset_manifest.get("train_image_count", 0)),
                "val_image_count": int(dataset_manifest.get("val_image_count", 0)),
            }
        )

    (splits_dir / "train.txt").write_text("\n".join(combined_train) + ("\n" if combined_train else ""))
    (splits_dir / "val.txt").write_text("\n".join(combined_val) + ("\n" if combined_val else ""))
    _write_dataset_yaml(package_root, class_name)

    manifest = {
        "created_at": utc_now_iso(),
        "package_id": batch_id,
        "target_class_name": class_name,
        "class_map": {"0": class_name},
        "source_directory": str(source_dir),
        "source_count": len(package_sources),
        "image_count": len(combined_train) + len(combined_val),
        "label_count": len(combined_train) + len(combined_val),
        "train_image_count": len(combined_train),
        "val_image_count": len(combined_val),
        "frames_with_target_detections": total_frames_with_target_detections,
        "total_target_detections": total_target_detections,
        "sources": package_sources,
        "entries": combined_entries,
    }
    write_json(package_root / "manifest.json", manifest)
    return manifest


def process_file(
    source: str,
    edge_config_path: str,
    policy_config_path: str,
    output_root_override: str = "",
    vision_api_url_override: str = "",
    edge_config_overrides: Dict[str, Any] = None,
) -> Dict[str, Any]:
    edge_overrides = {}
    if output_root_override:
        edge_overrides["output_root"] = output_root_override
    if vision_api_url_override:
        edge_overrides["vision_api_url"] = vision_api_url_override
    if edge_config_overrides:
        edge_overrides.update(edge_config_overrides)

    edge_config = load_edge_config(edge_config_path, overrides=edge_overrides)
    policy_config = load_policy_config(policy_config_path)

    source_path = expand_path(source)
    output_root = expand_path(edge_config.output_root)
    bundle_root = ensure_dir(output_root / edge_config.bundle_subdir)
    run_root = ensure_dir(output_root / edge_config.run_subdir)
    upload_root = ensure_dir(output_root / edge_config.upload_subdir)

    clip_id = _clip_id_for_source(source_path)
    run_id = _run_id(clip_id)
    run_started_at = utc_now_iso()
    run_dir = ensure_dir(run_root / run_id)

    client = VisionApiClient(edge_config.vision_api_url)
    job_payload, windowing = _build_job_payload(edge_config, source_path)
    accepted = client.submit_yolo_job(job_payload)
    write_json(run_dir / "vision_job_request.json", job_payload)
    write_json(run_dir / "vision_job_accepted.json", accepted)
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
            "run_started_at": run_started_at,
            "run_completed_at": utc_now_iso(),
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
            "vision_job_request": job_payload,
            "windowing_decision": windowing,
            "job_detection_summary": detections_summary,
            "bundle": bundle_record,
            "upload": upload_record,
        },
    )

    return {
        "clip_id": clip_id,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "selected": selected,
        "selection_reason": selection_reason,
        "bundle_dir": str(bundle_dir),
        "vision_job_id": result.job_id,
        "frame_count": len(frame_rows),
        "detection_count": len(tracked),
        "track_count": len(updated_tracks),
        "upload": upload_record,
    }


def smoke_test(
    source: str,
    edge_config_path: str,
    policy_config_path: str,
    output_root_override: str = "",
    vision_api_url_override: str = "",
    start_time_sec: float = 0.0,
    max_duration_sec: float = 3.0,
    frame_stride: int = 10,
    use_edge_window: bool = False,
) -> Dict[str, Any]:
    vision_request_overrides = {
        "output_mode": "dataset_package",
        "generate_preview_video": False,
    }
    requested_window = {
        "mode": "edge_config" if use_edge_window else "smoke_override",
        "start_time_sec": start_time_sec,
        "max_duration_sec": max_duration_sec,
        "frame_stride": frame_stride,
    }
    if not use_edge_window:
        vision_request_overrides.update(
            {
                "max_frames": None,
                "max_duration_sec": max_duration_sec,
                "start_time_sec": start_time_sec,
                "frame_stride": frame_stride,
            }
        )

    result = process_file(
        source=source,
        edge_config_path=edge_config_path,
        policy_config_path=policy_config_path,
        output_root_override=output_root_override,
        vision_api_url_override=vision_api_url_override,
        edge_config_overrides={"vision_request": vision_request_overrides},
    )
    pipeline_summary = read_json(Path(result["run_dir"]) / "pipeline_summary.json")
    job_detection_summary = pipeline_summary.get("job_detection_summary") or {}
    return {
        "ok": True,
        "source": source,
        "run_id": result["run_id"],
        "run_dir": result["run_dir"],
        "vision_job_id": result["vision_job_id"],
        "selected": result["selected"],
        "selection_reason": result["selection_reason"],
        "frame_count": result["frame_count"],
        "detection_count": result["detection_count"],
        "track_count": result["track_count"],
        "requested_window": requested_window,
        "job_detection_summary": job_detection_summary,
        "windowing_decision": pipeline_summary.get("windowing_decision"),
    }


def process_directory(
    source_dir: str,
    edge_config_path: str,
    policy_config_path: str,
    output_root_override: str = "",
    vision_api_url_override: str = "",
    package_name: str = "",
) -> Dict[str, Any]:
    edge_overrides = {
        "vision_request": {"output_mode": "dataset_package", "generate_preview_video": False},
    }
    if output_root_override:
        edge_overrides["output_root"] = output_root_override
    if vision_api_url_override:
        edge_overrides["vision_api_url"] = vision_api_url_override

    edge_config = load_edge_config(edge_config_path, overrides=edge_overrides)
    source_dir_path = expand_path(source_dir)
    sources = _list_video_sources(source_dir_path)
    output_root = expand_path(edge_config.output_root)
    package_id = package_name or _package_id_for_directory(source_dir_path)
    package_root = output_root / "ultralytics_packages" / package_id
    if package_root.exists():
        raise RuntimeError("PACKAGE_ROOT_ALREADY_EXISTS: {}".format(str(package_root)))

    source_results = []
    for source_path in sources:
        result = process_file(
            source=str(source_path),
            edge_config_path=edge_config_path,
            policy_config_path=policy_config_path,
            output_root_override=output_root_override,
            vision_api_url_override=vision_api_url_override,
            edge_config_overrides={"vision_request": edge_overrides["vision_request"]},
        )
        run_dir = Path(result["run_dir"])
        vision_job_manifest = read_json(run_dir / "vision_job_manifest.json")
        dataset_manifest_path_value = vision_job_manifest.get("dataset_manifest_path")
        if not dataset_manifest_path_value:
            raise RuntimeError("VISION_API_DATASET_MANIFEST_MISSING: {}".format(str(run_dir / "vision_job_manifest.json")))
        dataset_manifest_path = Path(dataset_manifest_path_value)
        if not dataset_manifest_path.exists():
            raise FileNotFoundError("VISION_API_DATASET_MANIFEST_NOT_FOUND: {}".format(str(dataset_manifest_path)))
        source_results.append(
            {
                "source_path": str(source_path),
                "clip_id": result["clip_id"],
                "run_id": result["run_id"],
                "vision_job_id": result["vision_job_id"],
                "selected": result["selected"],
                "selection_reason": result["selection_reason"],
                "dataset_root": str(dataset_manifest_path.parent),
                "dataset_manifest_path": str(dataset_manifest_path),
                "dataset_manifest": read_json(dataset_manifest_path),
            }
        )

    combined_manifest = _combine_source_datasets(
        package_root=package_root,
        batch_id=package_id,
        source_dir=source_dir_path,
        source_results=source_results,
    )
    return {
        "ok": True,
        "source_dir": str(source_dir_path),
        "source_count": len(source_results),
        "package_id": package_id,
        "package_root": str(package_root),
        "manifest_path": str(package_root / "manifest.json"),
        "image_count": combined_manifest["image_count"],
        "label_count": combined_manifest["label_count"],
        "train_image_count": combined_manifest["train_image_count"],
        "val_image_count": combined_manifest["val_image_count"],
        "sources": [
            {
                "source_path": item["source_path"],
                "clip_id": item["clip_id"],
                "run_id": item["run_id"],
                "vision_job_id": item["vision_job_id"],
                "dataset_manifest_path": item["dataset_manifest_path"],
                "selected": item["selected"],
                "selection_reason": item["selection_reason"],
            }
            for item in source_results
        ],
    }
