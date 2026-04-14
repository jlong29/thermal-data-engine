from dataclasses import replace
from typing import Dict, List, Optional, Tuple

from thermal_data_engine.common.models import DetectionRecord, TrackingConfig


def _bbox_tuple(record: DetectionRecord) -> Tuple[float, float, float, float]:
    return (record.bbox_left, record.bbox_top, record.bbox_right, record.bbox_bottom)


def bbox_iou(left: Tuple[float, float, float, float], right: Tuple[float, float, float, float]) -> float:
    inter_left = max(left[0], right[0])
    inter_top = max(left[1], right[1])
    inter_right = min(left[2], right[2])
    inter_bottom = min(left[3], right[3])
    inter_width = max(0.0, inter_right - inter_left)
    inter_height = max(0.0, inter_bottom - inter_top)
    inter_area = inter_width * inter_height
    if inter_area <= 0.0:
        return 0.0
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union_area = left_area + right_area - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def assign_track_ids(records: List[DetectionRecord], config: TrackingConfig) -> List[DetectionRecord]:
    active_tracks = {}
    next_track_idx = 1
    output = []

    grouped = {}
    for record in records:
        grouped.setdefault(record.frame_idx, []).append(record)

    for frame_idx in sorted(grouped.keys()):
        frame_records = grouped[frame_idx]
        expired = []
        for track_id, state in active_tracks.items():
            if frame_idx - state["last_frame_idx"] > config.max_gap_frames:
                expired.append(track_id)
        for track_id in expired:
            active_tracks.pop(track_id, None)

        available_track_ids = list(active_tracks.keys())
        used_track_ids = set()

        for record in frame_records:
            best_track_id = None
            best_iou = -1.0
            for track_id in available_track_ids:
                if track_id in used_track_ids:
                    continue
                state = active_tracks[track_id]
                score = bbox_iou(_bbox_tuple(record), state["bbox"])
                if score > best_iou:
                    best_iou = score
                    best_track_id = track_id
            if best_track_id is not None and best_iou >= config.iou_match_threshold:
                assigned_track_id = best_track_id
            else:
                assigned_track_id = "track-{:04d}".format(next_track_idx)
                next_track_idx += 1
            used_track_ids.add(assigned_track_id)
            updated = replace(record, track_id=assigned_track_id)
            active_tracks[assigned_track_id] = {
                "bbox": _bbox_tuple(updated),
                "last_frame_idx": frame_idx,
            }
            output.append(updated)
    return output

