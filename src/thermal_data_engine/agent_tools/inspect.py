from pathlib import Path
from typing import Any, Dict, List

from thermal_data_engine.common.io import read_json


def _created_at(item: Dict[str, Any]) -> str:
    return item.get("created_at") or item.get("run_completed_at") or item.get("run_started_at") or item.get("run_id", "")


def _bundle_manifests(root: Path) -> List[Dict[str, Any]]:
    manifests = []
    bundle_root = root / "bundles"
    if not bundle_root.exists():
        return manifests
    for manifest_path in sorted(bundle_root.glob("*/clip_manifest.json")):
        manifests.append(read_json(manifest_path))
    return manifests


def _run_summaries(root: Path) -> List[Dict[str, Any]]:
    rows = []
    run_root = root / "runs"
    if not run_root.exists():
        return rows
    for summary_path in sorted(run_root.glob("*/pipeline_summary.json")):
        payload = read_json(summary_path)
        payload["run_dir"] = str(summary_path.parent)
        rows.append(payload)
    return rows


def recent_bundles(root: str, limit: int = 5) -> List[Dict[str, Any]]:
    rows = sorted(_bundle_manifests(Path(root)), key=_created_at, reverse=True)
    return rows[:limit]


def recent_clips(root: str, limit: int = 5) -> List[Dict[str, Any]]:
    return recent_bundles(root, limit=limit)


def ambiguous_bundles(root: str, limit: int = 5) -> List[Dict[str, Any]]:
    rows = []
    for item in _bundle_manifests(Path(root)):
        if item.get("selection_reason") in ("unstable_track_motion", "edge_activity"):
            rows.append(item)
    rows = sorted(rows, key=lambda item: item.get("created_at", ""), reverse=True)
    return rows[:limit]


def ambiguous_clips(root: str, limit: int = 5) -> List[Dict[str, Any]]:
    return ambiguous_bundles(root, limit=limit)


def detector_summary(root: str) -> Dict[str, Any]:
    manifests = _bundle_manifests(Path(root))
    model_versions = {}
    selected_count = 0
    for item in manifests:
        model_versions[item.get("model_version", "unknown")] = model_versions.get(item.get("model_version", "unknown"), 0) + 1
        if item.get("selected"):
            selected_count += 1
    return {
        "bundle_count": len(manifests),
        "selected_count": selected_count,
        "model_versions": model_versions,
    }


def model_version(root: str) -> Dict[str, Any]:
    manifests = sorted(_bundle_manifests(Path(root)), key=_created_at)
    model_versions = sorted({item.get("model_version", "unknown") for item in manifests})
    latest_model = manifests[-1].get("model_version", "unknown") if manifests else None
    return {
        "latest_model_version": latest_model,
        "known_model_versions": model_versions,
        "bundle_count": len(manifests),
    }


def recent_runs(root: str, limit: int = 5) -> List[Dict[str, Any]]:
    rows = sorted(_run_summaries(Path(root)), key=_created_at, reverse=True)
    return rows[:limit]


def clip_artifact_summary(root: str) -> Dict[str, Any]:
    counts = {}
    for item in _bundle_manifests(Path(root)):
        clip_artifact = item.get("extra", {}).get("clip_artifact", {})
        mode = clip_artifact.get("write_mode", "unknown")
        counts[mode] = counts.get(mode, 0) + 1
    return {
        "bundle_count": sum(counts.values()),
        "clip_write_modes": counts,
    }


def upload_summary(root: str, limit: int = 10) -> Dict[str, Any]:
    counts = {}
    recent = recent_runs(root, limit=limit)
    for item in recent:
        upload = item.get("upload") or {}
        status = upload.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return {
        "recent_run_count": len(recent),
        "upload_statuses": counts,
    }


def edge_status(root: str) -> Dict[str, Any]:
    root_path = Path(root)
    bundle_root = root_path / "bundles"
    run_root = root_path / "runs"
    upload_root = root_path / "uploads"
    runs = recent_runs(root, limit=1)
    latest_run = runs[0] if runs else None
    return {
        "root_exists": root_path.exists(),
        "bundle_count": len(list(bundle_root.glob("*/clip_manifest.json"))) if bundle_root.exists() else 0,
        "run_count": len([item for item in run_root.iterdir() if item.is_dir()]) if run_root.exists() else 0,
        "upload_dir_exists": upload_root.exists(),
        "latest_run_dir": None if latest_run is None else latest_run.get("run_dir"),
        "latest_run": latest_run,
        "clip_artifacts": clip_artifact_summary(root),
        "uploads": upload_summary(root),
    }
