import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


WORKSPACE_ROOT = Path.home() / ".openclaw" / "workspace"
DATASETS_ROOT = WORKSPACE_ROOT / "datasets"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with open(path, "w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    with open(path, "w") as handle:
        handle.write(text)


def expand_path(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def path_relative_to_root(path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return str(resolved_path.relative_to(resolved_root))
    except ValueError:
        raise ValueError("PATH_OUTSIDE_ROOT: {} not under {}".format(str(resolved_path), str(resolved_root)))


def _parse_ffprobe_fps(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            numerator_value = float(numerator)
            denominator_value = float(denominator)
        except ValueError:
            return None
        if denominator_value == 0:
            return None
        return numerator_value / denominator_value
    try:
        return float(value)
    except ValueError:
        return None


def probe_video_metadata(path: Path) -> Dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError("FFPROBE_FAILED: {}".format(proc.stderr.strip() or proc.returncode))

    payload = json.loads(proc.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        return {}

    stream = streams[0]
    avg_fps = _parse_ffprobe_fps(stream.get("avg_frame_rate"))
    raw_fps = _parse_ffprobe_fps(stream.get("r_frame_rate"))
    duration = stream.get("duration")
    nb_frames = stream.get("nb_frames")

    return {
        "width": int(stream.get("width", 0) or 0),
        "height": int(stream.get("height", 0) or 0),
        "fps": avg_fps or raw_fps,
        "avg_frame_rate": stream.get("avg_frame_rate"),
        "r_frame_rate": stream.get("r_frame_rate"),
        "duration_sec": None if duration in (None, "") else float(duration),
        "nb_frames": None if nb_frames in (None, "") else int(nb_frames),
    }


def parquet_backend():
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        return None, None
    return pa, pq


def write_parquet_rows(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    pa, pq = parquet_backend()
    if pa is None or pq is None:
        raise RuntimeError("PARQUET_BACKEND_MISSING: install thermal-data-engine[parquet] or pyarrow")
    row_list = list(rows)
    table = pa.Table.from_pylist(row_list)
    ensure_dir(path.parent)
    pq.write_table(table, path)
