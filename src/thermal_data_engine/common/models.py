import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VisionRequestConfig:
    job_label_prefix: str = "thermal_edge"
    model_profile: str = "yolo11_person_v1"
    output_mode: str = "dataset_package_plus_preview_video"
    confidence_threshold: float = 0.25
    frame_stride: int = 5
    max_frames: Optional[int] = 2000
    max_duration_sec: Optional[float] = None
    start_time_sec: float = 0.0
    suspicious_fps_threshold: float = 120.0
    min_duration_sec_on_suspicious_fps: float = 5.0
    dataset_burst_gap_frames: int = 5
    generate_preview_video: bool = False
    overwrite: bool = False


@dataclass
class TrackingConfig:
    iou_match_threshold: float = 0.3
    max_gap_frames: int = 2
    min_track_frames: int = 2


@dataclass
class UploadConfig:
    enabled: bool = False
    backend: str = "local_copy"
    local_root: str = ""


@dataclass
class EdgeConfig:
    device_id: str = "edge-device-local"
    vision_api_url: str = "http://127.0.0.1:8000"
    output_root: str = "~/.openclaw/workspace/outputs/thermal_data_engine"
    bundle_subdir: str = "bundles"
    run_subdir: str = "runs"
    upload_subdir: str = "uploads"
    poll_interval_sec: float = 1.0
    poll_timeout_sec: float = 120.0
    copy_clip_source: bool = True
    write_run_record: bool = True
    vision_request: VisionRequestConfig = field(default_factory=VisionRequestConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)


@dataclass
class PolicyConfig:
    min_clip_frames: int = 3
    min_track_frames: int = 3
    high_confidence_threshold: float = 0.65
    jitter_threshold: float = 0.55
    edge_fraction_threshold: float = 0.35
    allow_empty_clip: bool = False
    keep_reason_labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class DetectionRecord:
    clip_id: str
    frame_idx: int
    source_frame_num: int
    timestamp_sec: Optional[float]
    track_id: Optional[str]
    class_id: Optional[int]
    class_name: str
    confidence: float
    bbox_left: float
    bbox_top: float
    bbox_right: float
    bbox_bottom: float
    bbox_width: float
    bbox_height: float
    area_px: float
    source_id: int
    image_width: int
    image_height: int
    is_target_class: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrackSummary:
    clip_id: str
    track_id: str
    class_name: str
    class_id: Optional[int]
    duration_frames: int
    start_frame_idx: int
    end_frame_idx: int
    mean_conf: float
    min_conf: float
    max_conf: float
    bbox_area_mean: float
    bbox_jitter: float
    edge_fraction: float
    detection_density: float
    selection_reason: str
    selected: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BundleManifest:
    clip_id: str
    source_device_id: str
    source_path: str
    start_ts: Optional[str]
    end_ts: Optional[str]
    fps: Optional[float]
    frame_count: int
    width: int
    height: int
    model_version: str
    tracker_type: str
    storage_uri: str
    created_at: str
    selection_reason: str
    selected: bool
    vision_job_id: str
    run_id: str
    track_count: int
    detection_count: int
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
