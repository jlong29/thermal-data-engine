from thermal_data_engine.common.config import load_edge_config, load_policy_config


def test_load_edge_config_applies_nested_overrides(tmp_path):
    config_path = tmp_path / "edge.yaml"
    config_path.write_text(
        "\n".join(
            [
                'device_id: "nx-01"',
                'output_root: "~/tmp-output"',
                'tracking:',
                '  iou_match_threshold: 0.42',
                'upload:',
                '  enabled: true',
                '  local_root: "~/uploads"',
            ]
        )
    )

    config = load_edge_config(str(config_path), overrides={"vision_api_url": "http://edge.local:8000"})

    assert config.device_id == "nx-01"
    assert config.tracking.iou_match_threshold == 0.42
    assert config.vision_api_url == "http://edge.local:8000"
    assert str(config.output_root).endswith("tmp-output")
    assert str(config.upload.local_root).endswith("uploads")


def test_load_policy_config_merges_defaults(tmp_path):
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text("min_clip_frames: 10\n")

    policy = load_policy_config(str(policy_path))

    assert policy.min_clip_frames == 10
    assert policy.high_confidence_threshold == 0.65
    assert policy.keep_reason_labels == {}
