from typing import Dict, List

from thermal_data_engine.common.models import DetectionRecord, PolicyConfig, TrackSummary
from thermal_data_engine.edge.tracking import bbox_iou


def _is_edge_detection(record: DetectionRecord, margin_ratio: float = 0.1) -> bool:
    x_margin = record.image_width * margin_ratio
    y_margin = record.image_height * margin_ratio
    return (
        record.bbox_left <= x_margin
        or record.bbox_top <= y_margin
        or record.bbox_right >= (record.image_width - x_margin)
        or record.bbox_bottom >= (record.image_height - y_margin)
    )


def summarize_tracks(records: List[DetectionRecord], policy: PolicyConfig) -> List[TrackSummary]:
    grouped = {}
    for record in records:
        if not record.track_id:
            continue
        grouped.setdefault(record.track_id, []).append(record)

    summaries = []
    for track_id, items in sorted(grouped.items()):
        items = sorted(items, key=lambda item: item.frame_idx)
        confidences = [item.confidence for item in items]
        areas = [item.area_px for item in items]
        edge_count = len([item for item in items if _is_edge_detection(item)])
        ious = []
        for idx in range(1, len(items)):
            prev_item = items[idx - 1]
            next_item = items[idx]
            ious.append(
                bbox_iou(
                    (prev_item.bbox_left, prev_item.bbox_top, prev_item.bbox_right, prev_item.bbox_bottom),
                    (next_item.bbox_left, next_item.bbox_top, next_item.bbox_right, next_item.bbox_bottom),
                )
            )
        bbox_jitter = 1.0 - (sum(ious) / len(ious)) if ious else 0.0
        detection_density = float(len(items)) / float((items[-1].frame_idx - items[0].frame_idx) + 1)
        summaries.append(
            TrackSummary(
                clip_id=items[0].clip_id,
                track_id=track_id,
                class_name=items[0].class_name,
                class_id=items[0].class_id,
                duration_frames=len(items),
                start_frame_idx=items[0].frame_idx,
                end_frame_idx=items[-1].frame_idx,
                mean_conf=sum(confidences) / len(confidences),
                min_conf=min(confidences),
                max_conf=max(confidences),
                bbox_area_mean=sum(areas) / len(areas),
                bbox_jitter=bbox_jitter,
                edge_fraction=float(edge_count) / float(len(items)),
                detection_density=detection_density,
                selection_reason=policy.keep_reason_labels.get("no_selection", "no_track_met_policy"),
                selected=False,
            )
        )
    return summaries

