# AGENTS.md — <REPO_NAME>

You are an AI coding agent operating inside the `<REPO_NAME>` repository.

This file is **always-on guidance**. Keep it short, stable, and high-signal. If something is task-specific, it belongs in `.agent/TASK_BRIEF.md`, `.agent/MEMORY.md`, or other `.agent/` scratch artifacts, not here.

---

## How to instantiate this template in a new repo
This template is meant to be converted into a repo-specific `AGENTS.md` as one of the first tasks in a new repository.

When bootstrapping a new repo, the agent should:
1. Read the user’s project brief and the repo tree.
2. Replace the placeholders in the sections **before** `## Working agreement`.
3. Preserve all policy sections from `## Working agreement` onward unless the user explicitly changes them.
4. Generalize or prune sections that do not apply.
5. Identify the repo’s durable docs that play the roles described in `## Docs policy`.

---

## Mission
<Describe the repo’s purpose in 2–5 lines. Focus on what the codebase does, for whom, and the dominant workflow or system boundary.>

Examples:
- Train and evaluate <MODEL_TYPE> for <TASK>, using a <DATA_WORKFLOW> workflow.
- Build and operate <SYSTEM_NAME>, including <CORE_SUBSYSTEMS>.
- Provide tools and services for <PRIMARY_USE_CASE>.

## Source of truth
When docs and code disagree, trust these files:
- `<path/to/primary/entrypoint_or_cli>`
- `<path/to/core/runtime_or_train_logic>`
- `<path/to/secondary_runtime_or_eval_logic>`
- `<path/to/common/shared_logic>`
- `<path/to/config_or_schema_definition>`

Additional repo-specific rules:
- <example: Keep optional subsystem infrastructure available; do not remove it unless explicitly requested.>
- <example: Prefer metadata-first inference over hard-coded defaults.>
- <example: Preserve backward compatibility for configs, artifacts, APIs, or on-disk layouts.>

---

## Repo map

### High-signal code
- `<src_or_pkg_dir>/` — <core library / application code>
  - `<important_file_or_subdir>` — <why it matters>
  - `<important_file_or_subdir>` — <why it matters>
  - `<important_file_or_subdir>` — <why it matters>
- `<secondary_code_dir>/` — <evaluation / reporting / tooling / services>
- `<tests_dir>/` — <test suite>
- `<configs_or_schema_dir>/` — <configuration / schemas / manifests>

### Large/noisy dirs (do not scan by default)
Avoid expensive traversal unless explicitly needed:
- `<artifacts_or_models_dir>/`
- `<data_dir_pattern>/`
- `<logs_or_runtime_dir>/`
- `<generated_or_cache_dir>/`

Use targeted commands instead (e.g., `ls <dir>`, `find <dir> -maxdepth 2 ...`, `rg ...`) and keep outputs small.

---

## Core workflow (minimal commands)

### Build / prepare / ingest
```bash
<insert canonical setup, build, or data-preparation command>
```

### Main run / train / serve path
```bash
<insert canonical primary workflow command>
```

### Secondary workflow(s)
```bash
<insert canonical fine-tune / batch / deploy / report command>
```

### Evaluate / validate
```bash
<insert canonical evaluation, smoke-test, or validation command>
```

Notes:
- <call out required invariants, e.g. data layout assumptions, required companions, default modes, etc.>
- <call out important defaults or caveats.>

---

## Metadata contracts (important)
Document the contracts the agent must preserve. Examples:
- Inputs / outputs written to disk:
  - `<path_or_pattern>` writes `<artifact>`
  - `<path_or_pattern>` reads `<artifact>`
- Metadata or schema behavior:
  - <example: omitted CLI args are inferred from metadata>
  - <example: explicit CLI args override inferred defaults>
- Runtime invariants:
  - <example: preserve backward compatibility of config keys>
  - <example: never change reward semantics without explicit approval>

If this repo does not use metadata-driven behavior, replace this section with the relevant invariants/contracts.

---

## Tests (default)
Run the fastest meaningful checks first:
```bash
<insert canonical fast test command>
```

If the repo has special runtime issues, document the workaround here:
```bash
<insert env workaround if needed>
```

Optional additional checks:
```bash
<insert lint / typecheck / integration command if appropriate>
```

---

## Coding/style conventions
- <language/runtime version(s), if important>
- <naming/style conventions that should be preserved>
- Prefer minimal, localized diffs; avoid broad formatting-only changes unless requested.
- <linter / formatter / style-config rule if one exists>
- If no single formatter/linter is enforced, follow existing local style in touched files.

---

## Working agreement (four-phase execution)
### Phase 1 — Plan + Task Definition (read-only)
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
- If possible, run `/compact` before continuing (to preserve working memory).

Notes:
  - A template for `.agent/TASK_BRIEF.md` is already available and it is copied from `docs/codex/TASK_BRIEF_TEMPLATE.md`

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
   - Inform the user that you have completed the task and await instructions.

### Cleanup at task closeout
At completion:
1. Summarize “gotchas / decisions / commands / TODOs” and promote them to durable docs (see `Task completion / closeout procedure`).
2. Create a folder `docs/codex/tasks/<task_slug>` under `docs/codex/tasks`
  - e.g. <task_slug> = YYYYMMDD_HHMM_<short_topic>
3. Move `.agent/TASK_BRIEF.md` to `docs/codex/tasks/<task_slug>/`
4. Move `.agent/MEMORY.md`to `docs/codex/tasks/<task_slug>/`
5. Empty `.agent/logs/` (or delete the directory contents)
6. Write the closeout into `docs/codex/tasks/<task_slug>/CLOSEOUT.md`
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
  - A template for `.agent/MEMORY.md` is already available and it is copied from `docs/codex/MEMORY_TEMPLATE.md`

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
