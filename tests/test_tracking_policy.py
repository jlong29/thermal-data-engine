from thermal_data_engine.common.models import DetectionRecord, PolicyConfig, TrackingConfig
from thermal_data_engine.edge.policy import select_clip
from thermal_data_engine.edge.summarizer import summarize_tracks
from thermal_data_engine.edge.tracking import assign_track_ids


def _record(frame_idx, left, top, right, bottom, confidence=0.9):
    return DetectionRecord(
        clip_id="clip-1",
        frame_idx=frame_idx,
        source_frame_num=frame_idx,
        timestamp_sec=float(frame_idx),
        track_id=None,
        class_id=0,
        class_name="person",
        confidence=confidence,
        bbox_left=float(left),
        bbox_top=float(top),
        bbox_right=float(right),
        bbox_bottom=float(bottom),
        bbox_width=float(right - left),
        bbox_height=float(bottom - top),
        area_px=float((right - left) * (bottom - top)),
        source_id=0,
        image_width=320,
        image_height=240,
        is_target_class=True,
    )


def test_assign_track_ids_reuses_track_for_overlapping_boxes():
    records = [
        _record(0, 10, 10, 50, 60),
        _record(1, 12, 11, 52, 61),
        _record(2, 14, 12, 54, 62),
    ]

    tracked = assign_track_ids(records, TrackingConfig(iou_match_threshold=0.3, max_gap_frames=1, min_track_frames=2))

    assert len({item.track_id for item in tracked}) == 1


def test_summarize_and_select_clip_for_high_confidence_track():
    records = [
        _record(0, 10, 10, 50, 60, confidence=0.92),
        _record(1, 12, 11, 52, 61, confidence=0.88),
        _record(2, 14, 12, 54, 62, confidence=0.91),
    ]
    tracked = assign_track_ids(records, TrackingConfig())
    policy = PolicyConfig(
        min_clip_frames=3,
        min_track_frames=3,
        high_confidence_threshold=0.8,
        jitter_threshold=0.8,
        edge_fraction_threshold=0.8,
        allow_empty_clip=False,
        keep_reason_labels={"high_confidence": "high_confidence_track", "no_selection": "no_track_met_policy"},
    )

    summaries = summarize_tracks(tracked, policy)
    selected, reason, updated = select_clip(summaries, policy, frame_count=3)

    assert len(summaries) == 1
    assert selected is True
    assert reason == "high_confidence_track"
    assert updated[0].selected is True
    assert updated[0].selection_reason == "high_confidence_track"


def test_short_clip_is_rejected_before_track_logic():
    policy = PolicyConfig(min_clip_frames=5)

    selected, reason, updated = select_clip([], policy, frame_count=2)

    assert selected is False
    assert reason == "clip_too_short"
    assert updated == []
