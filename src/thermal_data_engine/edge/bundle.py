import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

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

    clip_write_mode = "segment_extract"
    if not extract_clip_segment(source_clip_path, clip_path, manifest.start_ts, manifest.end_ts):
        clip_write_mode = "source_copy"
        copy_clip(source_clip_path, clip_path)

    manifest.extra["clip_artifact"] = {
        "write_mode": clip_write_mode,
        "source_path": str(source_clip_path),
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
