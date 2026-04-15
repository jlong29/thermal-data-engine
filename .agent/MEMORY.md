# .agent/MEMORY.md (scratch)

**Task:** initial-edge-pipeline  
**Last updated:** 2026-04-14 21:07 EDT

## Goal / status
- Discovery complete enough to bootstrap Phase 1 implementation.
- Repo bootstrap and initial implementation are now in place.
- End-to-end processing now works against local `vision_api`.
- Non-selected runs are now inspectable through repo-local inspection helpers and CLI output, which closes the biggest observability gap from the `no_detections` bring-up run.
- Positive-detection verification is now demonstrated on the Corpus Christi sample using a bounded later window.

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
- `CorpusChristi_PM398_05Feb_11_20am.mp4` reports `1000 fps`, so bounded verification windows must be chosen carefully. With that metadata, `max_frames: 600` only covers `0.6s`, which explained the first empty run.

## Verification run
- Command(s): discovery reads, repo inspection, `git init`, branch creation, `python3 -m compileall src`, `python3 -m pytest tests`, `python3 -m pip install --user pyarrow`, `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect edge-status --root ~/.openclaw/workspace/outputs/thermal_data_engine`, `PYTHONPATH=src python3 -m thermal_data_engine.cli process-file --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000`.
- Outcome(s): compileall passed, pytest passed, pyarrow installed, CLI smoke test passed, full end-to-end run passed. The successful run produced `runs/clip-8aa62360d128-20260414T214812Z/` and ended with `selected=false` / `selection_reason=no_detections`.

## Latest increment
- Added `agent_tools.inspect.upload_summary()` and wired it into `inspect edge-status`, so the edge status view now rolls up recent upload outcomes instead of forcing operators to inspect only the latest run.
- Extended `tests/test_inspect.py` to cover the new upload rollup and refreshed the README run-record docs to mention the new inspect behavior.
- Validation: `python3 -m compileall src` and `python3 -m pytest tests` both passed after the change (10 passed). Pytest still emits the existing pyarrow/pandas integration warning, but tests remain green.
- Committed the increment as `5794f2d` (`Add upload summary to edge status inspect`).
- Added `configs/edge/corpus_verification.yaml` and used it to run the pipeline against `CorpusChristi_PM398_05Feb_11_20am.mp4` with `start_time_sec: 210.0` and `max_frames: 5000`, based on sampled-frame inspection and prior `vision_api` task-history clues.
- Verification result: `vision_api` emitted `102` person detections across `102` frames in a 5-second bounded window; the thermal pipeline retained the result as bundle `clip-4c2b3b029292` with `track_count=18`, `detection_count=247`, and `selection_reason=edge_activity`.
- Added `run_started_at` and `run_completed_at` to `pipeline_summary.json`, then switched inspect helpers to sort runs by those timestamps instead of lexicographic `run_id` order.
- Tightened inspection coverage with a timestamp-ordering regression test and updated the README run-summary docs.
- Validation: `python3 -m compileall src` and `python3 -m pytest tests` both passed after the change (11 passed). The existing pyarrow/pandas warning still appears, but the suite remains green.

## Next steps
- Consider a lower-memory or alternate profile fallback for especially constrained NX conditions, without breaking the stable `vision_api` contract.
- If a selected real run is available, verify `inspect clip-artifacts` against actual bundle output rather than only fixture-backed tests.
- Consider whether run inspection should surface a concise top-level latest-selection summary in addition to the full latest run payload.
