# .agent/MEMORY.md (scratch)

**Task:** low-memory-edge-profile  
**Last updated:** 2026-04-15 23:08 EDT

## Goal / status
- Smoke-test milestone completed and validated.
- Low-memory Xavier NX fallback profile is now implemented, documented, and covered by targeted config/smoke tests.
- Artifact-correctness follow-up is active. The first suspicious retained bundle was traced to a repo-local clip extraction bug, not yet to a `vision_api` boundary issue.

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
- A selected bundle can still have a bogus `clip.mp4` even when manifest/parquet structure looks coherent, because bundle extraction was using absolute source timestamps against `vision_api`'s already-bounded `runtime_input_path`.

## Verification run
- Command(s): `python3 -m compileall src`; `python3 -m pytest tests/test_config.py tests/test_smoke.py`
- Outcome(s): compileall passed, and targeted pytest passed (`6 passed`). Coverage now confirms `configs/edge/low_memory.yaml` stays bounded (`dataset_package`, preview off, `max_frames: null`, `max_duration_sec: 3.0`, `frame_stride: 10`) and that `smoke-test --use-edge-window` preserves the selected edge profile window instead of overriding it.

## Verification run
- Artifact check: inspected `~/.openclaw/workspace/outputs/thermal_data_engine/bundles/clip-4c2b3b029292/clip_manifest.json`, `ffprobe` on its `clip.mp4`, and parquet row counts.
- Observed: manifest/parquet counts were coherent (`detection_count=247`, `track_count=18`), but `clip.mp4` was only `0.077s` with `77` frames at `1000/1` fps because bundle extraction sought to `210s` inside a 5-second bounded runtime clip.
- Fix: `src/thermal_data_engine/edge/bundle.py` now converts manifest timestamps to runtime-relative offsets when the source clip is the `vision_api` bounded input, and records the resolved clip window in `clip_artifact` metadata.
- Validation: `python3 -m compileall src`; `python3 -m pytest tests/test_bundle.py tests/test_smoke.py tests/test_config.py` (`11 passed`).

## Verification run
- Command(s): `python3 -m compileall src`; `python3 -m pytest tests/test_inspect.py tests/test_bundle.py tests/test_smoke.py tests/test_config.py`
- Outcome(s): compileall passed, targeted pytest passed (`16 passed`). Added `inspect ultralytics-package` as a lightweight readiness validator for the current Ultralytics-style dataset contract and wrote `docs/ULTRALYTICS_PACKAGE_CHECKLIST.md` as the staged thermal-owned package/file-plan handoff for tomorrow's hotter-machine smoke test.

## Verification run
- Command(s): `PYTHONPATH=src python3 -m thermal_data_engine.cli process-file --source /home/myclaw/.openclaw/workspace/datasets/incoming/CorpusChristi_PM398_05Feb_11_20am.mp4 --output-root /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000`; `ffprobe -v error -show_entries format=duration:stream=index,codec_name,codec_type,r_frame_rate,avg_frame_rate,nb_frames,width,height -of json /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/bundles/clip-4c2b3b029292/clip.mp4`; `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect ultralytics-package --path /home/myclaw/.openclaw/workspace/outputs/inference_jobs/yolo_20260415_230220_93e12e/dataset`
- Outcome(s): regenerated retained bundle now looks sane: manifest window `0.0 -> 4.995`, `clip.mp4` duration `4.997s`, `4997` video frames at `1000/1` fps, `detections.parquet` rows `29`, `tracks.parquet` rows `4`, and `extra.clip_artifact.timestamp_mode=runtime_relative_timestamps`. The structural Ultralytics validator also passed against the real reference dataset package after fixing a thermal-side parser gap for mapping-style `dataset.yaml` names entries (`names:\n  0: person`).

## Verification run
- Command(s): `python3 -m compileall src tests`; `python3 -m pytest tests/test_pipeline.py`; `python3 - <<'PY' ... urllib.request.urlopen('http://127.0.0.1:8000/health') / ('http://127.0.0.1:8001/health') ... PY`; attempted live commands updated to `PYTHONPATH=src python3 -m thermal_data_engine.cli ...`
- Outcome(s): compileall passed, targeted pipeline pytest passed (`3 passed`), and the repo-local folder-processing/combined-package code path is still present on disk. Live end-to-end validation remains blocked for this cron run because no reachable local `vision_api` was available: `http://127.0.0.1:8000/health` returned `404` and `http://127.0.0.1:8001/health` was connection refused. Also corrected the repo-local brief's live/package-check commands to include `PYTHONPATH=src`, which this checkout needs for direct module execution.

## Verification run
- Command(s): `PYTHONPATH=src python3 -m thermal_data_engine.cli process-directory --source-dir /home/myclaw/.openclaw/workspace/datasets/incoming --output-root /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine --vision-api-url http://127.0.0.1:8000 --package-name incoming-sample`; `PYTHONPATH=src python3 -m thermal_data_engine.cli inspect ultralytics-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-sample`
- Outcome(s): the live `vision_api` service on port `8000` was usable even though `/health` returned `404`. The batch run completed real per-file jobs for all three incoming MP4 files (`yolo_20260416_153143_b7d803`, `yolo_20260416_153346_b80436`, `yolo_20260416_153440_be4b87`). The outer CLI was interrupted before final package assembly, so I combined the completed per-job dataset packages into `outputs/thermal_data_engine/ultralytics_packages/incoming-sample/` from the recorded manifests. Validation then passed with `ok: true`, `29` images, `29` labels, `22` train entries, and `7` val entries.

## Gotchas discovered (promote at closeout)
- A `404` on `http://127.0.0.1:8000/health` is not a reliable blocker on this host; `/docs` and real job submission were the better liveness checks.
- If `process-directory` is interrupted after the last per-file `vision_api` job finishes, the combined-package write can be skipped and the last run directory can remain empty even though the underlying dataset package is already complete.
- Zero-label source videos are handled cleanly by the combined-package manifest, so downstream smoke tests should keep them as provenance-bearing inputs rather than filtering them out silently.

## Next steps
- Hand the validated package at `outputs/thermal_data_engine/ultralytics_packages/incoming-sample/` to the hotter-machine Ultralytics load/train smoke test.
- Reopen this repo only if that downstream consumer exposes a concrete package-compatibility problem.
