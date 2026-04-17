import pytest

from thermal_data_engine.vision_api.client import VisionApiClient, VisionApiError


def test_wait_for_job_retries_temporary_unreachable_error(monkeypatch):
    client = VisionApiClient("http://127.0.0.1:8000")
    calls = {"count": 0}

    def fake_get_job(job_id):
        calls["count"] += 1
        if calls["count"] == 1:
            raise VisionApiError("VISION_API_UNREACHABLE /v1/jobs/test: [Errno 111] Connection refused")
        return {"status": "completed", "output_dir": "/tmp/job"}

    monkeypatch.setattr(client, "get_job", fake_get_job)
    monkeypatch.setattr("thermal_data_engine.vision_api.client.time.sleep", lambda *_: None)

    result = client.wait_for_job("test", poll_interval_sec=0.01, timeout_sec=1.0)

    assert calls["count"] == 2
    assert result.status == "completed"
    assert result.output_dir == "/tmp/job"


def test_wait_for_job_retries_temporary_status_read_error(monkeypatch):
    client = VisionApiClient("http://127.0.0.1:8000")
    calls = {"count": 0}

    def fake_get_job(job_id):
        calls["count"] += 1
        if calls["count"] < 3:
            raise VisionApiError("VISION_API_HTTP_ERROR 503 /v1/jobs/test: {\"detail\":\"JOB_STATUS_TEMPORARILY_UNREADABLE\"}")
        return {"status": "completed", "output_dir": "/tmp/job"}

    monkeypatch.setattr(client, "get_job", fake_get_job)
    monkeypatch.setattr("thermal_data_engine.vision_api.client.time.sleep", lambda *_: None)

    result = client.wait_for_job("test", poll_interval_sec=0.01, timeout_sec=1.0)

    assert calls["count"] == 3
    assert result.status == "completed"


def test_wait_for_job_raises_non_retriable_error(monkeypatch):
    client = VisionApiClient("http://127.0.0.1:8000")

    monkeypatch.setattr(
        client,
        "get_job",
        lambda job_id: (_ for _ in ()).throw(VisionApiError("VISION_API_HTTP_ERROR 404 /v1/jobs/test: not found")),
    )
    monkeypatch.setattr("thermal_data_engine.vision_api.client.time.sleep", lambda *_: None)

    with pytest.raises(VisionApiError, match="404"):
        client.wait_for_job("test", poll_interval_sec=0.01, timeout_sec=1.0)
