from pathlib import Path
from typing import Any, Dict, List

from thermal_data_engine.common.io import read_json


def _bundle_manifests(root: Path) -> List[Dict[str, Any]]:
    manifests = []
    bundle_root = root / "bundles"
    if not bundle_root.exists():
        return manifests
    for manifest_path in sorted(bundle_root.glob("*/clip_manifest.json")):
        manifests.append(read_json(manifest_path))
    return manifests


def recent_bundles(root: str, limit: int = 5) -> List[Dict[str, Any]]:
    rows = sorted(_bundle_manifests(Path(root)), key=lambda item: item.get("created_at", ""), reverse=True)
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
    manifests = _bundle_manifests(Path(root))
    model_versions = sorted({item.get("model_version", "unknown") for item in manifests})
    latest_model = manifests[-1].get("model_version", "unknown") if manifests else None
    return {
        "latest_model_version": latest_model,
        "known_model_versions": model_versions,
        "bundle_count": len(manifests),
    }


def edge_status(root: str) -> Dict[str, Any]:
    root_path = Path(root)
    bundle_root = root_path / "bundles"
    run_root = root_path / "runs"
    upload_root = root_path / "uploads"
    latest_run = None
    if run_root.exists():
        run_dirs = sorted([item for item in run_root.iterdir() if item.is_dir()], key=lambda item: item.name)
        if run_dirs:
            latest_run = str(run_dirs[-1])
    return {
        "root_exists": root_path.exists(),
        "bundle_count": len(list(bundle_root.glob("*/clip_manifest.json"))) if bundle_root.exists() else 0,
        "run_count": len([item for item in run_root.iterdir() if item.is_dir()]) if run_root.exists() else 0,
        "upload_dir_exists": upload_root.exists(),
        "latest_run_dir": latest_run,
    }
