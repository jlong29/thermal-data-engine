## TASK_BRIEF

### Task
- Align `thermal-data-engine` with the external `~/openclawInfo` storage boundary while preserving current repo-local execution entrypoints.

### Why this update
- Workspace cleanup moved bulky outputs and datasets out of `~/.openclaw/workspace`, but this repo still points live defaults, configs, and operator docs at the old workspace-local paths and still stores its `.venv` inside the workspace.

### Fixed invariants (do not change)
- Keep `vision_api` as the detector/runtime boundary.
- Preserve runnable repo-local commands such as `.venv/bin/python` and `PYTHONPATH=src ...` where practical.
- Keep this task focused on storage/runtime hygiene, not pipeline redesign.

### Goal
- Update live defaults/docs to the external output boundary and move bulky env storage out of the workspace without breaking the established local command surface.

### Success criteria
- [x] Live default output roots no longer assume `~/.openclaw/workspace/outputs/...`.
- [x] Repo-local `.venv` storage is externalized under `~/openclawInfo` while `.venv` entrypoints in the repo remain usable.
- [x] Stable operator-facing docs/configs are updated where they would otherwise be misleading.
- [x] Minimal CLI verification passes through the preserved repo-local entrypoint.

### Relevant files (why)
- `src/thermal_data_engine/common/models.py` — live default output-root authority
- `configs/edge/*.yaml` — live operator-facing config defaults
- `AGENTS.md` and `README.md` — durable repo workflow and operator guidance

### Refined Phase 2 Plan
1) Externalize the actual `.venv` directory while preserving the repo-local symlink entrypoint.
2) Update live output/data defaults in code, configs, and stable docs to use `~/openclawInfo` roots.
3) Run minimal CLI verification through the preserved repo-local entrypoint.

### Small change sets (execution order)
1) Storage move plus compatibility symlink for `.venv`
2) Path-default updates in code/config/docs
3) Minimal verification and notes cleanup

### Verification
- Fast: `python3 -m compileall src`
- Targeted: `PYTHONPATH=src .venv/bin/python -m pytest tests`
- Full: `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect recent --root ~/openclawInfo/outputs/thermal_data_engine`

### Risks / gotchas
- Live configs under `configs/edge/` will drift from reality if the external output boundary is not updated consistently.
- Historical archive docs can keep old paths, but stable repo guidance should not.

### Decision rule for defaults
- Prefer external roots for bulky artifacts, but keep repo-local command ergonomics stable when a symlinked entrypoint avoids unnecessary churn.

### Deferred work note
- Do not redesign clip policy, upload policy, or vision API integration in this task.

### Current status
- Complete. Live output defaults now resolve under `~/.openclawInfo`, the actual env directory now lives under `~/openclawInfo/venvs/thermal-data-engine/`, the repo-local `.venv` entrypoint remains usable as a symlink, and minimal verification passed.
