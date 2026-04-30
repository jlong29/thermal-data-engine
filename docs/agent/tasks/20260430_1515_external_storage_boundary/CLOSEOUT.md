# CLOSEOUT

## Summary
Aligned `thermal-data-engine` with the external `~/openclawInfo` storage boundary while preserving the established repo-local command surface.

## Decisions made
- Moved the live default output root from `~/.openclaw/workspace/outputs/thermal_data_engine` to `~/.openclawInfo/outputs/thermal_data_engine`.
- Updated live configs and stable operator docs to use `~/.openclawInfo/datasets/...` and `~/.openclawInfo/outputs/...`.
- Externalized the actual repo virtualenv directory under `~/openclawInfo/venvs/thermal-data-engine/`.
- Preserved `.venv` in the repo as a symlink entrypoint so existing commands still work.
- Updated `.gitignore` so the symlink entrypoint remains ignored cleanly.

## New invariants / gotchas
- Bulky output and environment storage should live outside the workspace, while the repo keeps a stable runnable surface.
- Live edge config defaults must match the real storage boundary or operator guidance drifts immediately.
- Historical archive docs can keep old examples, but stable repo guidance should not.

## New/changed commands
- Existing repo-local commands remain valid, including `PYTHONPATH=src .venv/bin/python ...`.
- Live default output root now resolves to `~/.openclawInfo/outputs/thermal_data_engine`.

## Verification evidence
- `python3 -m compileall src`
- `PYTHONPATH=src .venv/bin/python -m pytest tests`
- `PYTHONPATH=src .venv/bin/python - <<'PY' ... from thermal_data_engine.common.models import EdgeConfig ... PY`

Results:
- compileall passed
- pytest suite passed, 31 tests
- `EdgeConfig().output_root` resolved to `~/.openclawInfo/outputs/thermal_data_engine`

## TODO / follow-up
- Historical repo task archives were intentionally left mostly untouched unless they were part of the live operator-facing surface.
- Push/review can happen from branch `workspace-cleanup-external-storage` when desired.
