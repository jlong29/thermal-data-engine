# Ultralytics Package Checklist

Use this as the concrete contract for the next thermal-owned packaging slice and for tomorrow's hotter-machine smoke test.

## Current compatibility target

Until `thermal-data-engine` owns package creation directly, treat the current `vision_api` dataset package as the compatibility reference, not the final ownership boundary.

Reference layout:

```text
<dataset_root>/
├─ images/
├─ labels/
├─ splits/
│  ├─ train.txt
│  └─ val.txt
├─ dataset.yaml
└─ manifest.json
```

## Required readiness checks

- `dataset.yaml` exists and includes `path`, `train`, `val`, and `names`
- `splits/train.txt` and `splits/val.txt` exist
- every split entry resolves to an image under the dataset root
- every referenced image has a matching label `.txt`
- every label row is `class x_center y_center width height`
- class ids are non-negative integers
- normalized coordinates stay within `[0, 1]`
- `manifest.json` is present when available so provenance survives the boundary shift

## CLI helper

```bash
python3 -m thermal_data_engine.cli inspect ultralytics-package \
  --path ~/.openclaw/workspace/outputs/inference_jobs/<job_id>/dataset
```

The helper is intentionally lightweight. It does not run Ultralytics itself. It gives a bounded structural readiness check before the hotter-machine load/train smoke test.

## Tomorrow's smoke-test handoff target

A thermal-owned package is ready for the hotter-machine smoke test when:

1. the validator returns `"ok": true`
2. the package still traces back to retained thermal artifacts and run metadata
3. a real Ultralytics load/train smoke test can point at the emitted `dataset.yaml` without re-deciding layout details

## File-plan for the thermal-owned slice

When package creation moves here, keep it staged:

1. consume retained bundle metadata plus the relevant bounded source imagery
2. write the same training-facing layout under a thermal-owned output root
3. preserve provenance in a thermal-owned `manifest.json`
4. compare the thermal-owned package against the current `vision_api` reference package before retiring the old path
