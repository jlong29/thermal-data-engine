# .agent/MEMORY.md (scratch)

**Task:** workspace-cleanup-external-storage  
**Last updated:** 2026-04-30 15:07 EDT

## Goal / status
- Repo-local cleanup task seeded from the workspace root task.

## Repro commands
- `du -sh .venv 2>/dev/null`
- `find . -path '*/.git' -prune -o -path '*/.venv*' -prune -o -type f \( -name '*.py' -o -name '*.md' -o -name '*.yaml' -o -name '*.yml' \) -print0 | xargs -0 grep -n "workspace/datasets\|workspace/outputs\|openclawInfo" 2>/dev/null`

## Hypotheses + evidence
- Preserving `.venv` as a repo-local symlink entrypoint should keep current commands working with minimal churn.

## Decisions (and why)
- Favor compatibility-preserving env relocation over forcing a new activation ritual.

## Gotchas discovered (promote at closeout)
- Live edge config defaults still point under the workspace and need deliberate cleanup.

## Verification run
- Command(s): `python3 -m compileall src`; `PYTHONPATH=src .venv/bin/python -m pytest tests`; `PYTHONPATH=src .venv/bin/python - <<'PY' ... from thermal_data_engine.common.models import EdgeConfig ... PY`
- Outcome(s): compileall passed, the 31-test pytest suite passed, and `EdgeConfig().output_root` now resolves to `~/.openclawInfo/outputs/thermal_data_engine`.

## Next steps
- Review remaining stable docs/configs for any old workspace-local path examples, then prepare repo-local closeout.
