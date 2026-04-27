# .agent/MEMORY.md (archived scratch)

**Task:** incoming_handoff_packages  
**Closed:** 2026-04-27

## Goal / status
- Completed. The Xavier edge node now produces both accepted downstream handoff packages for the incoming thermal-video folder.
- Phase 1 is accepted by the desktop consumer as the direct training contract.
- Phase 2 is accepted by the desktop consumer as the current temporal/provenance contract.

## Repro / verification commands
- `python3 -m compileall src tests`
- `python3 -m pytest tests`
- `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect ultralytics-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample`
- `PYTHONPATH=src .venv/bin/python -m thermal_data_engine.cli inspect video-package --path /home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/video_packages/incoming-video-sample`

## Decisions (and why)
- Kept `vision_api` as the detector/runtime boundary and moved downstream package ownership into `thermal-data-engine` in stages.
- Preserved a two-phase contract split: phase 1 trains now, phase 2 preserves temporal structure for later consumer-side work.
- Reused the existing stable bundle contract inside phase 2 instead of inventing a second raw temporal export format.

## Gotchas discovered
- A `.gitignore` entry does not stop Git from tracking files that were already committed. The thermal repo's `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` remained tracked until they were explicitly removed from the index.
- Desktop smoke-train failure was caused by Ultralytics path handling on the consumer side, not corrupted edge packages. That fix belongs in the desktop repo, not here.
- Phase 2 should be described honestly as a temporal substrate, not overclaimed as a direct training contract.

## Durable evidence
- Phase 1 package: `/home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/ultralytics_packages/incoming-training-sample`
- Phase 2 package: `/home/myclaw/.openclaw/workspace/outputs/thermal_data_engine/video_packages/incoming-video-sample`
- Desktop acceptance note: `/home/myclaw/.openclaw/workspace/src/vision-trainer/docs/handoffs/DESKTOP_TO_EDGE.md`

## Next steps
- Reopen this repo only if the desktop consumer requests an explicit contract change or a new edge-side producer capability.
