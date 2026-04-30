# AGENTS.md - thermal-data-engine

You are an AI coding agent operating inside the `thermal-data-engine` repository.

This file is always-on guidance. Keep it short, stable, and high-signal. If something is task-specific, it belongs in `.agent/TASK_BRIEF.md`, `.agent/MEMORY.md`, or other `.agent/` scratch artifacts, not here.

---

## Mission
`thermal-data-engine` is the edge-side thermal video capture and triage pipeline for OpenClaw.
It turns raw thermal video into structured clip bundles, track summaries, and lightweight inspection outputs while keeping `vision_api` as the detector/runtime boundary.
Phase 1 focuses on bounded offline file processing with conservative defaults that can later be extended into a longer-running edge service.

## Source of truth
When docs and code disagree, trust these files:
- `src/thermal_data_engine/cli.py` - CLI entrypoints and user-facing workflow
- `src/thermal_data_engine/edge/pipeline.py` - main offline processing path
- `src/thermal_data_engine/vision_api/client.py` - `vision_api` integration boundary
- `src/thermal_data_engine/common/models.py` - stable bundle and record schemas
- `src/thermal_data_engine/common/config.py` - config loading and defaults

Additional repo-specific rules:
- Keep this repo edge-side only; do not add training, CVAT, or desktop orchestration.
- Preserve `vision_api` as the detector/runtime boundary; do not copy its DeepStream control logic here.
- Preserve stable bundle contents: `clip.mp4`, `detections.parquet`, `tracks.parquet`, `clip_manifest.json`.
- Keep Python 3.8-compatible syntax and typing where practical.
- Prefer inspectable defaults and explicit artifacts over hidden background behavior.

---

## Repo map

### High-signal code
- `src/thermal_data_engine/` - main package
  - `common/` - schemas, config models, serialization, shared utilities
  - `vision_api/` - local HTTP client for job submission and polling
  - `edge/` - detection loading, tracking, summarization, policy, bundling, upload, pipeline
  - `agent_tools/` - local inspection helpers over saved artifacts
- `configs/` - default edge runtime and clip-policy configs
- `tests/` - focused unit tests
- `README.md` - repo overview and runnable commands

### Large/noisy dirs (do not scan by default)
Avoid expensive traversal unless explicitly needed:
- `.git/`
- `.venv/`
- `~/.openclawInfo/datasets/`
- `~/.openclawInfo/outputs/`
- `__pycache__/`

Use targeted commands and keep output small.

---

## Core workflow (minimal commands)

### Build / prepare
```bash
python3 -m pip install -e .[dev]
```

### Main run path
```bash
python3 -m thermal_data_engine.cli process-file \
  --source ~/.openclawInfo/datasets/incoming/example.mp4 \
  --output-root ~/.openclawInfo/outputs/thermal_data_engine
```

### Secondary workflows
```bash
python3 -m thermal_data_engine.cli inspect recent --root ~/.openclawInfo/outputs/thermal_data_engine
python3 -m thermal_data_engine.cli inspect ambiguous --root ~/.openclawInfo/outputs/thermal_data_engine
```

### Validate
```bash
python3 -m compileall src
python3 -m pytest tests
```

Notes:
- `vision_api` must be running separately for end-to-end processing.
- Bundle writing requires an available parquet backend such as `pyarrow`.
- Every task starts at the workspace layer. If this repo is active under a workspace task, expect `~/.openclaw/workspace/ACTIVE_TASK.md` to exist first and treat this repo's `.agent/TASK_BRIEF.md` as a seeded local subtask, not a standalone top-level task.

---

## Metadata contracts (important)
- Inputs / outputs written to disk:
  - `configs/edge/*.yaml` and `configs/data/*.yaml` define runtime and policy defaults.
  - `<output_root>/runs/<run_id>/` stores pipeline run records and copied `vision_api` job metadata.
  - `<output_root>/bundles/<clip_id>/` stores `clip.mp4`, parquet artifacts, and `clip_manifest.json`.
  - `<output_root>/uploads/` stores local upload copies and upload records when enabled.
- Runtime invariants:
  - `vision_api` is called over HTTP and remains the detector boundary.
  - `detections.jsonl` is treated as the source detection artifact from `vision_api`.
  - Bundle schemas and manifest keys should stay backward compatible once emitted.

---

## Tests (default)
Run the fastest meaningful checks first:
```bash
python3 -m compileall src
python3 -m pytest tests
```

---

## Coding/style conventions
- Python 3.8 compatibility matters.
- Use explicit dataclasses and typed helper functions for inspectable behavior.
- Prefer localized diffs; avoid broad formatting-only changes.
- Keep IO separate from pure selection/tracking logic where practical.

---

## Working agreement (four-phase execution)
### Phase 1 — Plan + Task Definition
Goal: build repo-aware understanding and produce **one** task artifact.

Rules:
- Do not edit code or tracked files in this phase.
- Use ≤10 shell commands and keep output concise (avoid long listings).
- Restate goal + success criteria.
- Identify the minimal relevant files and why.
- Propose a plan + verification commands.

**Phase 1 output (the only artifact):**
- Create a branch for the task using a short name reflecting the goal of the task e.g. `add-oAuth`, `fix-callbacks`
- Write the plan to: `.agent/TASK_BRIEF.md`

`.agent/` is **untracked** and exists specifically for this ephemeral brief. The brief may be updated in Phase 2.

At the end of Phase 1:
- Ensure `.agent/TASK_BRIEF.md` is up to date.

Notes:
  - A template for `.agent/TASK_BRIEF.md` is already available and it is copied from `docs/agent/TASK_BRIEF_TEMPLATE.md`

### Phase 2 — Implement + Learn (write + verify, no git history operations)
Goal: Execute the plan developed in Phase 1 and memorialized in `.agent/TASK_BRIEF.md`

Rules:
- You may edit files, but do NOT run:
  `git merge`/`rebase`, `git reset --hard`, `git clean -fd`
- Keep diffs minimal; no broad “format-only” changes unless requested.
- After each coherent edit set:
  1) state intent + files touched
  2) apply changes
  3) run verification and report results
  4) show diff summary and key hunks

## Phase 3 — Debug mode
Goal: Review the output of Phase 2 and thoroughly test until all outputs are predictable and functional.

When debugging bugs introduced during Phase 2, follow this strict loop:
1) Reproduce the failure with the exact command provided.
2) Minimize the repro (smallest failing command/test).
3) Propose 1–2 hypotheses and what evidence would confirm each.
4) Add a targeted regression test when feasible.
5) Make a **surgical** fix (minimal files), re-run the failing test(s), then broaden coverage.
6) Update `.agent/TASK_BRIEF.md` with what changed and why; if possible, run `/compact` if context is getting large.

## Phase 4 — Task completion / closeout procedure
Goal: Summary successful completed work and clean up.

When the task is complete (as defined in `.agent/TASK_BRIEF.md`), the agent should:
1) Review this `AGENTS.md`.
2) Produce a **closeout summary** (short, high-signal), using `.agent/MEMORY.md` and `.agent/TASK_BRIEF.md` as the sources of truth:
   - Decisions made (and why)
   - New invariants/gotchas discovered
   - New/changed commands (CLI flags, scripts)
   - TODOs / follow-ups
   - Verification evidence (commands run)
3) Update repo docs **only when the information is stable and reusable**:
   - Update `AGENTS.md` for durable workflow/invariants only.
   - Create or Update `docs/PROJECT_STATE.md` for “current operational workflow.”
   - Create or Update `docs/MODULE_MAP.md` if module boundaries/entrypoints changed.
   - Create or Update `docs/METRICS_AND_DIAGNOSTICS.md` if diagnostics/metrics interpretation changed.
   - Finish with `git status` and commit message(s)
   - commit code
4) Follow the procedure defined in `Cleanup at task closeout` (defined below)

### Cleanup at task closeout
At completion:
1. Summarize “gotchas / decisions / commands / TODOs” and promote them to durable docs (see `Task completion / closeout procedure`).
2. Create a folder `docs/agent/tasks/<task_slug>` under `docs/agent/tasks`
  - e.g. <task_slug> = YYYYMMDD_HHMM_<short_topic>
3. Move `.agent/TASK_BRIEF.md` to `docs/agent/tasks/<task_slug>/`
4. Move `.agent/MEMORY.md` to `docs/agent/tasks/<task_slug>/`
5. Empty `.agent/logs/` (or delete the directory contents)
6. Write the closeout into `docs/agent/tasks/<task_slug>/CLOSEOUT.md`
7. Verify: `.agent/TASK_BRIEF.md` and `.agent/MEMORY.md` exist (templates), `.agent/logs/` empty, and archive folder contains `TASK_BRIEF.md`, `MEMORY.md`, and `CLOSEOUT.md`

---

## `.agent/` folder policy (scratch only)

`.agent/` is **untracked** and is intended as **scratch space only**. It should be safe to delete at any time, and it should be **cleared at task closeout**.

### Purpose
1) **Task Related documents** most notably TASK_BRIEF.md
2) **User-provided artifacts for debugging** (logs, traces, perf output) that the agent should inspect.
3) **Agent working memory externalization** when the chat context window is under pressure.

> Policy: when the agent learns a new *gotcha* during Phase 2, it should record it in `.agent/MEMORY.md` and only promote it to durable docs during closeout.

### Flat structure (preferred)
- `.agent/TASK_BRIEF.md` — compact task description, success criteria, and progress notes
- `.agent/MEMORY.md` — compact running notes related to the work process rather than the task definition itself
- `.agent/logs/` — log files and small extracted snippets

### `.agent/TASK_BRIEF.md`
During Phase 2 this document may be updated to reflect changes in:

- **Goal / status**
- **Decisions (and why)**
- **Next steps**

### `.agent/MEMORY.md` format (keep it small)
Maintain **≤ 200 lines** when possible. Use bullets. Suggested headings:

- **A valuable research url cache**
- **Repro commands**
- **Hypotheses + evidence**
- **Failed experiments and ideas**
- **Gotchas discovered**  ← (promote these during closeout)
- **Verification run** (commands + outcomes)

Notes:
  - A template for `.agent/MEMORY.md` is already available and it is copied from `docs/agent/MEMORY_TEMPLATE.md`

### Log naming convention
Store logs as:

- `.agent/logs/YYYYMMDD_HHMM_<topic>.log`

The agent may create filtered snippets alongside logs, e.g.:

- `.agent/logs/YYYYMMDD_HHMM_<topic>__excerpt.log`
- `.agent/logs/YYYYMMDD_HHMM_<topic>__grep_<pattern>.log`

Keep snippets **small** (e.g., ≤ 500 lines). Do not copy huge logs.

### When to externalize to `.agent/`
Externalize (write/update `.agent/MEMORY.md`) when any of these is true:
- The plan has evolved materially beyond Phase 1.
- Debugging involves multiple hypotheses or long traces.
- The session is getting long (check `/status` or a token status line).
- The agent is about to run `/compact`.

After externalizing:
- Update `.agent/MEMORY.md`
- Then run `/compact` to keep interactive context focused.

---

## Docs policy (protect the context window)
Do NOT read the entire docs tree by default.

Open docs only when needed, in this priority order:
1) The repo’s current workflow / operational workflow doc
2) The repo’s module / architecture map doc
3) The repo’s metrics / diagnostics doc
4) The repo’s experiment log / change log / results log

Treat these as historical unless explicitly requested:
- old specs
- old work plans
- archived project-state headers
- other superseded planning docs

If the repo does not yet have durable docs in these roles, ask the user which files are intended to fill them.
