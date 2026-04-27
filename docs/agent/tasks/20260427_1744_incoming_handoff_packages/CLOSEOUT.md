# Closeout: incoming handoff packages

## Summary
This repo-local task is complete.

`thermal-data-engine` now owns the Xavier-side folder-to-handoff packaging flow for both:
- phase 1, a direct Ultralytics-style image dataset
- phase 2, a provenance-rich temporal video package

Both packages were validated on-device, then accepted by the desktop consumer. The only meaningful integration bug found during desktop smoke training was consumer-side Ultralytics path resolution, which was fixed in `vision-trainer` without changing the upstream edge package contract.

## Decisions made
- Kept `vision_api` as the detector/runtime boundary and made thermal the package producer.
- Treated phase 1 as the immediate training contract and phase 2 as the temporal/provenance substrate for later downstream conversion or tracking-aware work.
- Preserved package-contract stability once the desktop consumer accepted the current phase 1 and phase 2 formats.

## New invariants / gotchas
- Current phase 1 and phase 2 formats are accepted by the desktop consumer. Do not casually change manifest fields or layout.
- If a future package change affects the shared contract, update the contract docs, schema files, and validators together on the consumer side and record the change through `vision-trainer/docs/handoffs/`.
- `.gitignore` does not retroactively untrack files; committed `.agent` files had to be removed from the Git index explicitly.

## Verification evidence
- `python3 -m compileall src tests`
- `python3 -m pytest tests`
- `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect ultralytics-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample`
- `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect video-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/video_packages/incoming-video-sample`
- Desktop downstream acceptance: `../vision-trainer/docs/handoffs/DESKTOP_TO_EDGE.md`

## Acceptance status
- Edge-side implementation: complete
- On-device structural validation: complete
- Desktop phase 1 smoke validation: complete
- Desktop single-GPU smoke training: complete
- Desktop 3-GPU smoke training: complete
- Desktop phase 2 structural acceptance: complete

## Follow-up
- Future work should move through the shared `vision-trainer` coordination surface.
- Reopen `thermal-data-engine` only for explicit producer-side changes, contract changes, or new edge capabilities.
