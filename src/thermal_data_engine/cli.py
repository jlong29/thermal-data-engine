import argparse
import json
from typing import Any

from thermal_data_engine.agent_tools.inspect import (
    ambiguous_clips,
    clip_artifact_summary,
    detector_summary,
    edge_status,
    model_version,
    recent_clips,
    recent_runs,
)
from thermal_data_engine.edge.pipeline import process_file
from thermal_data_engine.edge.pipeline import smoke_test


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thermal-data-engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process-file")
    process_parser.add_argument("--source", required=True)
    process_parser.add_argument("--edge-config", default="configs/edge/default.yaml")
    process_parser.add_argument("--policy-config", default="configs/data/clip_policy.yaml")
    process_parser.add_argument("--output-root", default="")
    process_parser.add_argument("--vision-api-url", default="")

    smoke_parser = subparsers.add_parser("smoke-test")
    smoke_parser.add_argument("--source", required=True)
    smoke_parser.add_argument("--edge-config", default="configs/edge/default.yaml")
    smoke_parser.add_argument("--policy-config", default="configs/data/clip_policy.yaml")
    smoke_parser.add_argument("--output-root", default="")
    smoke_parser.add_argument("--vision-api-url", default="")
    smoke_parser.add_argument("--start-time-sec", type=float, default=0.0)
    smoke_parser.add_argument("--max-duration-sec", type=float, default=3.0)
    smoke_parser.add_argument("--frame-stride", type=int, default=10)
    smoke_parser.add_argument("--use-edge-window", action="store_true")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_subparsers = inspect_parser.add_subparsers(dest="inspect_command", required=True)

    recent_parser = inspect_subparsers.add_parser("recent")
    recent_parser.add_argument("--root", required=True)
    recent_parser.add_argument("--limit", type=int, default=5)

    ambiguous_parser = inspect_subparsers.add_parser("ambiguous")
    ambiguous_parser.add_argument("--root", required=True)
    ambiguous_parser.add_argument("--limit", type=int, default=5)

    model_version_parser = inspect_subparsers.add_parser("model-version")
    model_version_parser.add_argument("--root", required=True)

    detector_parser = inspect_subparsers.add_parser("detector")
    detector_parser.add_argument("--root", required=True)

    clip_artifacts_parser = inspect_subparsers.add_parser("clip-artifacts")
    clip_artifacts_parser.add_argument("--root", required=True)

    status_parser = inspect_subparsers.add_parser("edge-status")
    status_parser.add_argument("--root", required=True)

    runs_parser = inspect_subparsers.add_parser("runs")
    runs_parser.add_argument("--root", required=True)
    runs_parser.add_argument("--limit", type=int, default=5)

    return parser


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "process-file":
        result = process_file(
            source=args.source,
            edge_config_path=args.edge_config,
            policy_config_path=args.policy_config,
            output_root_override=args.output_root,
            vision_api_url_override=args.vision_api_url,
        )
        _print_json(result)
        return

    if args.command == "smoke-test":
        result = smoke_test(
            source=args.source,
            edge_config_path=args.edge_config,
            policy_config_path=args.policy_config,
            output_root_override=args.output_root,
            vision_api_url_override=args.vision_api_url,
            start_time_sec=args.start_time_sec,
            max_duration_sec=args.max_duration_sec,
            frame_stride=args.frame_stride,
            use_edge_window=args.use_edge_window,
        )
        _print_json(result)
        return

    if args.command == "inspect":
        if args.inspect_command == "recent":
            _print_json(recent_clips(args.root, limit=args.limit))
            return
        if args.inspect_command == "ambiguous":
            _print_json(ambiguous_clips(args.root, limit=args.limit))
            return
        if args.inspect_command == "detector":
            _print_json(detector_summary(args.root))
            return
        if args.inspect_command == "clip-artifacts":
            _print_json(clip_artifact_summary(args.root))
            return
        if args.inspect_command == "model-version":
            _print_json(model_version(args.root))
            return
        if args.inspect_command == "edge-status":
            _print_json(edge_status(args.root))
            return
        if args.inspect_command == "runs":
            _print_json(recent_runs(args.root, limit=args.limit))
            return

    parser.error("unsupported command")


if __name__ == "__main__":
    main()
