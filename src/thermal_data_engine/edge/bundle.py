import shutil
from pathlib import Path
from typing import Dict, List

from thermal_data_engine.common.io import ensure_dir, parquet_backend, write_json, write_parquet_rows
from thermal_data_engine.common.models import BundleManifest, DetectionRecord, TrackSummary


def copy_clip(source_path: Path, destination_path: Path) -> None:
    ensure_dir(destination_path.parent)
    shutil.copy2(str(source_path), str(destination_path))


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

    copy_clip(source_clip_path, clip_path)
    write_parquet_rows(detections_path, [item.to_dict() for item in detections])
    write_parquet_rows(tracks_path, [item.to_dict() for item in tracks])
    write_json(manifest_path, manifest.to_dict())

    return {
        "clip_path": str(clip_path),
        "detections_path": str(detections_path),
        "tracks_path": str(tracks_path),
        "manifest_path": str(manifest_path),
    }

