import shutil
from pathlib import Path
from typing import Dict

from thermal_data_engine.common.io import ensure_dir, write_json
from thermal_data_engine.common.models import UploadConfig


def upload_bundle(bundle_dir: Path, upload_root: Path, config: UploadConfig, clip_id: str) -> Dict[str, str]:
    if not config.enabled:
        return {"status": "disabled", "uri": ""}
    if config.backend != "local_copy":
        raise RuntimeError("UPLOAD_BACKEND_UNSUPPORTED: {}".format(config.backend))

    target_root = Path(config.local_root) if config.local_root else upload_root / "local"
    target_dir = target_root / clip_id
    if target_dir.exists():
        shutil.rmtree(str(target_dir))
    ensure_dir(target_dir.parent)
    shutil.copytree(str(bundle_dir), str(target_dir))
    record = {"status": "uploaded", "uri": str(target_dir), "backend": config.backend}
    write_json(target_dir / "upload_record.json", record)
    return record

