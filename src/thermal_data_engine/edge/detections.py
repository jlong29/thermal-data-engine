from typing import Any, Dict, List

from thermal_data_engine.common.models import DetectionRecord


def flatten_detection_records(frame_rows: List[Dict[str, Any]], clip_id: str) -> List[DetectionRecord]:
    rows = []
    for frame_idx, frame_row in enumerate(frame_rows):
        detections = frame_row.get("target_detections") or frame_row.get("detections") or []
        for detection in detections:
            bbox_xyxy = detection.get("bbox_xyxy") or {}
            bbox_xywh = detection.get("bbox_xywh") or {}
            rows.append(
                DetectionRecord(
                    clip_id=clip_id,
                    frame_idx=frame_idx,
                    source_frame_num=int(frame_row.get("frame_num", frame_idx)),
                    timestamp_sec=frame_row.get("source_timestamp_sec", frame_row.get("timestamp_sec")),
                    track_id=None,
                    class_id=detection.get("class_id"),
                    class_name=detection.get("class_name", "unknown"),
                    confidence=float(detection.get("confidence", 0.0)),
                    bbox_left=float(bbox_xyxy.get("left", 0.0)),
                    bbox_top=float(bbox_xyxy.get("top", 0.0)),
                    bbox_right=float(bbox_xyxy.get("right", 0.0)),
                    bbox_bottom=float(bbox_xyxy.get("bottom", 0.0)),
                    bbox_width=float(bbox_xywh.get("width", 0.0)),
                    bbox_height=float(bbox_xywh.get("height", 0.0)),
                    area_px=float(detection.get("area_px", 0.0)),
                    source_id=int(frame_row.get("source_id", 0)),
                    image_width=int(frame_row.get("image_width", 0)),
                    image_height=int(frame_row.get("image_height", 0)),
                    is_target_class=bool(detection.get("is_target_class", True)),
                )
            )
    return rows

