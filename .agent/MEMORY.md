# .agent/MEMORY.md (scratch)

**Task:** initial-edge-pipeline  
**Last updated:** 2026-04-14 18:33 EDT

## Goal / status
- Discovery complete enough to bootstrap Phase 1 implementation.
- Repo bootstrap and initial implementation are now in place.
- End-to-end processing now works against local `vision_api`.
- Non-selected runs are now inspectable through repo-local inspection helpers and CLI output, which closes the biggest observability gap from the `no_detections` bring-up run.

## Repro commands
- `git init && git checkout -b feature/initial-edge-pipeline`
- `find . -maxdepth 2 -type f | sort`
- `find ../vision_api -maxdepth 2 -type f | sort | head -200`

## Hypotheses + evidence
- `thermal-data-engine` should stay edge-side only. Evidence: `Design_draft.md`, `TASK_BRIEF_draft.md`.
- `vision_api` should remain the detector/control boundary. Evidence: design draft notes plus existing `vision_api` FastAPI job API and `detections.jsonl` artifact layout.
- Phase 1 needs local tracking because `vision_api` emits detections without persistent track IDs. Evidence: `vision_api/app/runner.py` writes per-frame detections only.

## Decisions (and why)
- Initialize `thermal-data-engine` as its own git repo, because sibling repos under `src/` are git repos and the user prefers per-task branching.
- Start with an offline file-processing pipeline instead of pretending realtime service support is already validated.
- Keep implementation Python-first and config-driven, matching repo drafts and Xavier constraints.

## Gotchas discovered (promote at closeout)
- `thermal-data-engine` did not yet have a `.git/` directory or `AGENTS.md`.
- The outer workspace git still exists, but sibling repos under `src/` are independently versioned.
- `rg` is unavailable on this host, so bounded discovery currently relies on `find`, `grep`, `sed`, and selective file reads.
- Initial NX bring-up should avoid preview rendering. The earlier default `dataset_package_plus_preview_video` hit a DeepStream/NVVIC memory allocation failure; switching to `dataset_package` with a smaller `max_frames` allowed end-to-end completion.

## Verification run
- Command(s): discovery reads, repo inspection, `git init`, branch creation, `python3 -m compileall src`, `python3 -m pytest tests`, `python3 -m pip install --user pyarrow`, `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect edge-status --root ~/.openclaw/workspace/outputs/thermal_data_engine`, `PYTHONPATH=src python3 -m thermal_data_engine.cli process-file --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000`.
- Outcome(s): compileall passed, pytest passed, pyarrow installed, CLI smoke test passed, full end-to-end run passed. The successful run produced `runs/clip-8aa62360d128-20260414T214812Z/` and ended with `selected=false` / `selection_reason=no_detections`.

## Latest increment
- Added run-level inspection in `agent_tools.inspect` by reading `runs/*/pipeline_summary.json`.
- Added CLI support for `python3 -m thermal_data_engine.cli inspect runs --root ...`.
- Expanded `edge-status` to include the latest run summary, so operators can immediately see whether the most recent run was selected and why.
- Enriched `pipeline_summary.json` with quick-troubleshooting metadata: `source_path`, `model_version`, `frame_window`, `frame_count`, `detection_count`, `track_count`, and `job_detection_summary`.
- Added test coverage for richer run summaries and updated README notes.
- Validation: `python3 -m compileall src` and `python3 -m pytest tests` both passed after the change.

## Next steps
- Decide whether the next increment should add real clip extraction instead of copying the bounded input clip as the saved `clip.mp4`.
- Consider a lower-memory or alternate profile fallback for especially constrained NX conditions, without breaking the stable `vision_api` contract.
- Consider surfacing upload status in `pipeline_summary.json` too, so a single run summary captures selection, artifact volume, and local handoff outcome.
