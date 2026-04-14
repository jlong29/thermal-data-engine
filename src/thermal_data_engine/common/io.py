import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


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
