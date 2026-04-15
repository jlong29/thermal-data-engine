# .agent/MEMORY.md (scratch)

**Task:** low-memory-edge-profile  
**Last updated:** 2026-04-14 22:00 EDT

## Goal / status
- Smoke-test milestone completed and validated.
- New active repo-local task seeded: add a lower-memory or fallback runtime profile for constrained NX bring-up.

## Repro commands
- `python3 -m compileall src`
- `python3 -m pytest tests`
- `PYTHONPATH=src python3 -m thermal_data_engine.cli smoke-test --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8001 --max-duration-sec 3.0`

## Hypotheses + evidence
- A named lower-memory profile is the next highest-value edge-side increment.
  - Evidence: real NX bring-up already hit `Couldn't create nvvic Session: Cannot allocate memory`, and the bootstrap plan still calls for lightweight deployment validation on the edge node.
- The smoke-test path should make lower-memory validation easier to exercise once the profile exists.
  - Evidence: the new smoke-test CLI already gives us a fast bounded validation harness without needing a full manual process-file command.

## Decisions (and why)
- Keep this as a thermal-data-engine task on the existing unmerged branch, because it is an adjacent edge-side improvement within the same Xavier NX bring-up slice.

## Gotchas discovered (promote at closeout)
- If a repo-local brief is left fully checked off after a milestone, the isolated progress runner will correctly stop. The next concrete repo-local task has to be written down explicitly to keep overnight progress honest.
- The smoke-test path is now real, so future edge bring-up refinements should prefer validating through it before inventing more ad hoc one-off commands.

## Verification run
- Command(s): `python3 -m compileall src`; `python3 -m pytest tests`; `PYTHONPATH=src python3 -m thermal_data_engine.cli smoke-test --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8001 --max-duration-sec 3.0`
- Outcome(s): compileall passed, pytest passed (`16 passed`), and the real smoke test completed successfully with a bounded 3-second run (`run_id=clip-8aa62360d128-20260415T015958Z`, `ok=true`, `selected=false`, `detection_count=0`, `frame_count=15`).

## Next steps
- Inspect which runtime knobs are the cleanest lower-memory candidates, then add a named profile under `configs/edge/`.
