# .agent/MEMORY.md (scratch)

**Task:** initial-edge-pipeline  
**Last updated:** 2026-04-14 17:10 EDT

## Goal / status
- Discovery complete enough to bootstrap Phase 1 implementation.
- Repo bootstrap and initial implementation are now in place.
- Unit validation passed locally; end-to-end processing is waiting on a running local `vision_api` service.

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

## Verification run
- Command(s): discovery reads, repo inspection, `git init`, branch creation, `python3 -m compileall src`, `python3 -m pytest tests`, `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect edge-status --root ~/.openclaw/workspace/outputs/thermal_data_engine`.
- Outcome(s): compileall passed, pytest passed (7 passed, 1 skipped because `pyarrow` is missing), CLI smoke test passed.

## Next steps
- Start or point at a running local `vision_api` service and run an end-to-end `process-file` pass.
- Install `pyarrow` if parquet bundle writing needs to be exercised end to end on this host.
- Decide whether the next increment should add real clip extraction instead of copying the bounded input clip as the saved `clip.mp4`.
