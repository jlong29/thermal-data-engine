import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from thermal_data_engine.common.io import ensure_dir, parquet_backend, write_json, write_parquet_rows
from thermal_data_engine.common.models import BundleManifest, DetectionRecord, TrackSummary


def copy_clip(source_path: Path, destination_path: Path) -> None:
    ensure_dir(destination_path.parent)
    shutil.copy2(str(source_path), str(destination_path))


def _clip_duration_sec(start_ts: Optional[str], end_ts: Optional[str]) -> Optional[float]:
    if start_ts in (None, "") or end_ts in (None, ""):
        return None
    duration = float(end_ts) - float(start_ts)
    if duration <= 0:
        return None
    return duration


def _format_timestamp(value: float) -> str:
    return "{:.6f}".format(value).rstrip("0").rstrip(".") or "0"


def _resolve_clip_window(source_clip_path: Path, manifest: BundleManifest) -> Tuple[Optional[str], Optional[str], str]:
    clip_start = manifest.start_ts
    clip_end = manifest.end_ts
    window_mode = "manifest_timestamps"

    vision_job_manifest = manifest.extra.get("vision_job_manifest") or {}
    runtime_input_path = vision_job_manifest.get("runtime_input_path")
    start_time_sec = vision_job_manifest.get("start_time_sec")
    if runtime_input_path and start_time_sec is not None:
        try:
            if Path(runtime_input_path).resolve() == source_clip_path.resolve():
                clip_start = _format_timestamp(max(0.0, float(manifest.start_ts or 0.0) - float(start_time_sec)))
                clip_end = _format_timestamp(max(0.0, float(manifest.end_ts or 0.0) - float(start_time_sec)))
                window_mode = "runtime_relative_timestamps"
        except (OSError, TypeError, ValueError):
            pass

    return clip_start, clip_end, window_mode


def extract_clip_segment(source_path: Path, destination_path: Path, start_ts: Optional[str], end_ts: Optional[str]) -> bool:
    duration = _clip_duration_sec(start_ts, end_ts)
    if duration is None:
        return False

    ensure_dir(destination_path.parent)
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start_ts),
        "-i",
        str(source_path),
        "-t",
        str(duration),
        "-c",
        "copy",
        str(destination_path),
    ]
    try:
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError:
        return False
    return completed.returncode == 0 and destination_path.exists()


def write_bundle(
    bundle_dir: Path,
    source_clip_path: Path,
    manifest: BundleManifest,
    detections: List[DetectionRecord],
    tracks: List[TrackSummary],
) -> Dict[str, str]:
    pa, pq = parquet_backend()
    if pa is None or pq is None:
        raise RuntimeError("PARQUET_BACKEND_MISSING: install thermal-data-engine[parquet] or pyarrow")

    ensure_dir(bundle_dir)
    clip_path = bundle_dir / "clip.mp4"
    detections_path = bundle_dir / "detections.parquet"
    tracks_path = bundle_dir / "tracks.parquet"
    manifest_path = bundle_dir / "clip_manifest.json"

    clip_start_ts, clip_end_ts, clip_window_mode = _resolve_clip_window(source_clip_path, manifest)

    clip_write_mode = "segment_extract"
    if not extract_clip_segment(source_clip_path, clip_path, clip_start_ts, clip_end_ts):
        clip_write_mode = "source_copy"
        copy_clip(source_clip_path, clip_path)

    manifest.extra["clip_artifact"] = {
        "write_mode": clip_write_mode,
        "source_path": str(source_clip_path),
        "clip_start_ts": clip_start_ts,
        "clip_end_ts": clip_end_ts,
        "timestamp_mode": clip_window_mode,
    }

    write_parquet_rows(detections_path, [item.to_dict() for item in detections])
    write_parquet_rows(tracks_path, [item.to_dict() for item in tracks])
    write_json(manifest_path, manifest.to_dict())

    return {
        "clip_path": str(clip_path),
        "detections_path": str(detections_path),
        "tracks_path": str(tracks_path),
        "manifest_path": str(manifest_path),
        "clip_write_mode": clip_write_mode,
    }
