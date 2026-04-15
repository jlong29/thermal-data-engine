# .agent/MEMORY.md (scratch)

**Task:** initial-edge-pipeline  
**Last updated:** 2026-04-14 20:02 EDT

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
- Surfaced bundle clip-write provenance in stable local artifacts: `edge.bundle.write_bundle()` now records `extra.clip_artifact.write_mode` plus the bundle source path in `clip_manifest.json`, and returns the mode to the caller.
- Extended `edge.pipeline` run summaries with a `bundle` section so selected runs explicitly report whether a bundle was written and whether `clip.mp4` came from segment extraction or source-copy fallback.
- Added `agent_tools.inspect.clip_artifact_summary()` and a matching `inspect clip-artifacts` CLI subcommand so operators can quickly see how bundles were produced without opening videos by hand.
- Updated focused tests for bundle metadata and inspect output, and refreshed README examples/docs for the new inspect surface.
- Validation: `python3 -m compileall src` and `python3 -m pytest tests` both passed after the change (10 passed). Pytest still emits the existing pyarrow/pandas integration warning, but tests remain green.

## Next steps
- Consider a lower-memory or alternate profile fallback for especially constrained NX conditions, without breaking the stable `vision_api` contract.
- Consider whether `inspect edge-status` should promote a small top-level upload summary, not just surface it inside `latest_run`.
- If a selected real run is available, verify `inspect clip-artifacts` against actual bundle output rather than only fixture-backed tests.
