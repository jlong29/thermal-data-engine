import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, request

from thermal_data_engine.common.io import read_json


class VisionApiError(RuntimeError):
    pass


@dataclass
class VisionJobResult:
    job_id: str
    status: str
    output_dir: str
    status_payload: Dict[str, Any]

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)

    @property
    def detections_path(self) -> Path:
        return self.output_path / "detections.jsonl"


class VisionApiClient(object):
    def __init__(self, base_url: str, timeout_sec: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def _request_json(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.base_url + path
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url=url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout_sec) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise VisionApiError("VISION_API_HTTP_ERROR {} {}: {}".format(exc.code, path, detail))
        except error.URLError as exc:
            raise VisionApiError("VISION_API_UNREACHABLE {}: {}".format(path, exc.reason))
        return json.loads(body or "{}")

    def submit_yolo_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request_json("POST", "/v1/jobs/yolo-inference", payload=payload)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        return self._request_json("GET", "/v1/jobs/{}".format(job_id))

    def _is_retriable_poll_error(self, exc: VisionApiError) -> bool:
        message = str(exc)
        return (
            "VISION_API_UNREACHABLE" in message
            or "VISION_API_HTTP_ERROR 500" in message
            or "VISION_API_HTTP_ERROR 502" in message
            or "VISION_API_HTTP_ERROR 503" in message
            or "JOB_STATUS_TEMPORARILY_UNREADABLE" in message
        )

    def wait_for_job(self, job_id: str, poll_interval_sec: float, timeout_sec: float) -> VisionJobResult:
        start = time.time()
        while True:
            try:
                status_payload = self.get_job(job_id)
            except VisionApiError as exc:
                if self._is_retriable_poll_error(exc):
                    if time.time() - start > timeout_sec:
                        raise VisionApiError("VISION_API_POLL_TIMEOUT {} after {:.1f}s".format(job_id, timeout_sec))
                    time.sleep(poll_interval_sec)
                    continue
                raise
            status = status_payload.get("status", "")
            if status == "completed":
                output_dir = status_payload.get("output_dir")
                if not output_dir:
                    raise VisionApiError("VISION_API_MISSING_OUTPUT_DIR: {}".format(job_id))
                return VisionJobResult(
                    job_id=job_id,
                    status=status,
                    output_dir=output_dir,
                    status_payload=status_payload,
                )
            if status == "failed":
                raise VisionApiError("VISION_API_JOB_FAILED {}: {}".format(job_id, json.dumps(status_payload, sort_keys=True)))
            if time.time() - start > timeout_sec:
                raise VisionApiError("VISION_API_POLL_TIMEOUT {} after {:.1f}s".format(job_id, timeout_sec))
            time.sleep(poll_interval_sec)

    def load_job_manifest(self, result: VisionJobResult) -> Dict[str, Any]:
        manifest_path = result.output_path / "manifest.json"
        if not manifest_path.exists():
            raise VisionApiError("VISION_API_MANIFEST_MISSING: {}".format(str(manifest_path)))
        return read_json(manifest_path)
