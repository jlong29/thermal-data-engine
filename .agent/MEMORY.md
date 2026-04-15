# .agent/MEMORY.md (scratch)

**Task:** low-memory-edge-profile  
**Last updated:** 2026-04-14 22:07 EDT

## Goal / status
- Smoke-test milestone completed and validated.
- Low-memory Xavier NX fallback profile is now implemented, documented, and covered by targeted config/smoke tests.

## Repro commands
- `python3 -m compileall src`
- `python3 -m pytest tests/test_config.py tests/test_smoke.py`
- `PYTHONPATH=src python3 -m thermal_data_engine.cli smoke-test --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8001 --max-duration-sec 3.0`
- `PYTHONPATH=src python3 -m thermal_data_engine.cli smoke-test --source ~/.openclaw/workspace/datasets/incoming/example.mp4 --edge-config configs/edge/low_memory.yaml --output-root ~/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8001 --use-edge-window`

## Hypotheses + evidence
- A named lower-memory profile is the next highest-value edge-side increment.
  - Evidence: real NX bring-up already hit `Couldn't create nvvic Session: Cannot allocate memory`, and the bootstrap plan still calls for lightweight deployment validation on the edge node.
- The smoke-test path should make lower-memory validation easier to exercise once the profile exists.
  - Evidence: a small `--use-edge-window` switch now lets smoke tests preserve the selected edge profile's own bounded runtime window instead of always replacing it.

## Decisions (and why)
- Keep this as a thermal-data-engine task on the existing unmerged branch, because it is an adjacent edge-side improvement within the same Xavier NX bring-up slice.
- Keep the default profile as the normal path, and add `configs/edge/low_memory.yaml` as an explicit fallback instead of silently weakening the default runtime request.
- Keep smoke-test defaults unchanged for quick bounded checks, and require explicit `--use-edge-window` opt-in when validating a named profile's own windowing.

## Gotchas discovered (promote at closeout)
- If a repo-local brief is left fully checked off after a milestone, the isolated progress runner will correctly stop. The next concrete repo-local task has to be written down explicitly to keep overnight progress honest.
- The smoke-test path is now real, so future edge bring-up refinements should prefer validating through it before inventing more ad hoc one-off commands.

## Verification run
- Command(s): `python3 -m compileall src`; `python3 -m pytest tests/test_config.py tests/test_smoke.py`
- Outcome(s): compileall passed, and targeted pytest passed (`6 passed`). Coverage now confirms `configs/edge/low_memory.yaml` stays bounded (`dataset_package`, preview off, `max_frames: null`, `max_duration_sec: 3.0`, `frame_stride: 10`) and that `smoke-test --use-edge-window` preserves the selected edge profile window instead of overriding it.

## Next steps
- If the user wants more confidence on real hardware, run a live NX smoke test with `configs/edge/low_memory.yaml` against the local `vision_api` service and capture the resulting run record.
