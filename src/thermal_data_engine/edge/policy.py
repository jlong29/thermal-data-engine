from typing import Dict, List, Tuple

from thermal_data_engine.common.models import PolicyConfig, TrackSummary


def select_clip(track_summaries: List[TrackSummary], policy: PolicyConfig, frame_count: int) -> Tuple[bool, str, List[TrackSummary]]:
    if frame_count < policy.min_clip_frames:
        return False, "clip_too_short", track_summaries
    if not track_summaries:
        return bool(policy.allow_empty_clip), "empty_clip" if policy.allow_empty_clip else "no_detections", track_summaries

    selected = False
    clip_reason = policy.keep_reason_labels.get("no_selection", "no_track_met_policy")
    updated = []

    for summary in track_summaries:
        reason = policy.keep_reason_labels.get("no_selection", "no_track_met_policy")
        is_selected = False
        if summary.duration_frames >= policy.min_track_frames and summary.mean_conf >= policy.high_confidence_threshold:
            reason = policy.keep_reason_labels.get("high_confidence", "high_confidence_track")
            is_selected = True
        elif summary.duration_frames >= policy.min_track_frames and summary.bbox_jitter >= policy.jitter_threshold:
            reason = policy.keep_reason_labels.get("unstable_motion", "unstable_track_motion")
            is_selected = True
        elif summary.duration_frames >= policy.min_track_frames and summary.edge_fraction >= policy.edge_fraction_threshold:
            reason = policy.keep_reason_labels.get("edge_activity", "edge_activity")
            is_selected = True
        updated_summary = TrackSummary(
            clip_id=summary.clip_id,
            track_id=summary.track_id,
            class_name=summary.class_name,
            class_id=summary.class_id,
            duration_frames=summary.duration_frames,
            start_frame_idx=summary.start_frame_idx,
            end_frame_idx=summary.end_frame_idx,
            mean_conf=summary.mean_conf,
            min_conf=summary.min_conf,
            max_conf=summary.max_conf,
            bbox_area_mean=summary.bbox_area_mean,
            bbox_jitter=summary.bbox_jitter,
            edge_fraction=summary.edge_fraction,
            detection_density=summary.detection_density,
            selection_reason=reason,
            selected=is_selected,
        )
        updated.append(updated_summary)
        if is_selected and not selected:
            clip_reason = reason
            selected = True

    return selected, clip_reason, updated

