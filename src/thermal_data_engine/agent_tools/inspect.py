import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from thermal_data_engine.common.io import read_json


_RUN_ID_TIMESTAMP_RE = re.compile(r"-(\d{8}T\d{6}Z)$")


def _created_at(item: Dict[str, Any]) -> str:
    run_id = item.get("run_id", "")
    match = _RUN_ID_TIMESTAMP_RE.search(run_id)
    run_id_timestamp = match.group(1) if match else ""
    return item.get("created_at") or item.get("run_completed_at") or item.get("run_started_at") or run_id_timestamp or run_id


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


def _resolve_dataset_entry(dataset_root: Path, dataset_path: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    if dataset_path.parent.joinpath(candidate).exists():
        return dataset_path.parent / candidate
    return dataset_root / candidate


def _parse_dataset_yaml(dataset_path: Path) -> Dict[str, str]:
    values = {}
    for raw_line in dataset_path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        values[key] = value
    return values


def _validate_label_file(label_path: Path) -> Tuple[bool, List[str], int]:
    errors = []
    object_count = 0
    for index, raw_line in enumerate(label_path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append("%s: line %d should have 5 columns, found %d" % (str(label_path), index, len(parts)))
            continue
        try:
            class_id = int(parts[0])
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append("%s: line %d contains non-numeric YOLO fields" % (str(label_path), index))
            continue
        if class_id < 0:
            errors.append("%s: line %d has negative class id" % (str(label_path), index))
        for coord in coords:
            if coord < 0.0 or coord > 1.0:
                errors.append("%s: line %d has coordinate outside [0, 1]" % (str(label_path), index))
                break
        object_count += 1
    return not errors, errors, object_count


def validate_ultralytics_package(path: str) -> Dict[str, Any]:
    dataset_root = Path(path)
    errors = []
    warnings = []
    split_counts = {}
    image_count = 0
    label_count = 0
    object_count = 0

    dataset_yaml_path = dataset_root / "dataset.yaml"
    labels_dir = dataset_root / "labels"
    images_dir = dataset_root / "images"
    train_split_path = dataset_root / "splits" / "train.txt"
    val_split_path = dataset_root / "splits" / "val.txt"

    for required_path in (dataset_root, dataset_yaml_path, images_dir, labels_dir, train_split_path, val_split_path):
        if not required_path.exists():
            errors.append("missing required path: %s" % str(required_path))

    dataset_fields = {}
    if dataset_yaml_path.exists():
        dataset_fields = _parse_dataset_yaml(dataset_yaml_path)
        for key in ("path", "train", "val", "names"):
            if key not in dataset_fields or dataset_fields[key] == "":
                errors.append("dataset.yaml missing required key: %s" % key)

    split_field_paths = []
    if dataset_fields:
        for split_name in ("train", "val"):
            split_value = dataset_fields.get(split_name)
            if split_value:
                split_field_paths.append((split_name, _resolve_dataset_entry(dataset_root, dataset_yaml_path, split_value)))

    for split_name, split_path in split_field_paths:
        if not split_path.exists():
            errors.append("dataset.yaml %s entry does not exist: %s" % (split_name, str(split_path)))
            continue
        if split_path.suffix == ".txt":
            entries = [line.strip() for line in split_path.read_text().splitlines() if line.strip()]
        else:
            entries = [str(path.relative_to(dataset_root)) for path in sorted(split_path.glob("*")) if path.is_file()]
        split_counts[split_name] = len(entries)
        for entry in entries:
            image_path = _resolve_dataset_entry(dataset_root, split_path, entry)
            if not image_path.exists():
                errors.append("%s split references missing image: %s" % (split_name, str(image_path)))
                continue
            image_count += 1
            try:
                relative_image = image_path.relative_to(images_dir)
            except ValueError:
                try:
                    relative_image = image_path.relative_to(dataset_root)
                except ValueError:
                    errors.append("%s split image is outside dataset root: %s" % (split_name, str(image_path)))
                    continue
            label_path = labels_dir / relative_image.with_suffix(".txt")
            if not label_path.exists():
                errors.append("missing label for image: %s" % str(image_path))
                continue
            label_count += 1
            valid_label, label_errors, label_objects = _validate_label_file(label_path)
            object_count += label_objects
            if not valid_label:
                errors.extend(label_errors)

    manifest_path = dataset_root / "manifest.json"
    if not manifest_path.exists():
        warnings.append("manifest.json missing, provenance metadata will be weaker")

    return {
        "ok": not errors,
        "dataset_root": str(dataset_root),
        "dataset_yaml": str(dataset_yaml_path),
        "required_paths": {
            "images": str(images_dir),
            "labels": str(labels_dir),
            "train_split": str(train_split_path),
            "val_split": str(val_split_path),
        },
        "dataset_fields": dataset_fields,
        "split_counts": split_counts,
        "image_count": image_count,
        "label_count": label_count,
        "object_count": object_count,
        "errors": errors,
        "warnings": warnings,
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
