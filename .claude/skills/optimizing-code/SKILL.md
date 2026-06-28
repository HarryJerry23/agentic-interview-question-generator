---
name: optimizing-code
description: Scans the whole project for dead code, unused functions/imports, orphan files and folders, and over-complex code, then suggests beginner-friendly, maintainable refactors. Produces a grouped findings report (safe deletions, refactor suggestions, needs-review) and applies changes ONLY after the user approves. Use when the user says "optimize the code", "clean up the codebase", "remove dead/unused code", "find unused functions", "make the code more maintainable / clearer / beginner-friendly", or "tidy the project structure".
---

# Optimizing code for clarity & maintainability

Make the project clean, maintainable, and beginner-friendly by removing what isn't used and
simplifying what's needlessly complex. **Report first, edit only after the user approves.**

## When this runs

Trigger on requests to optimize/clean/tidy the code, remove dead or unused code, or improve
maintainability/readability. Default scope: the `agentic-mcq-generation-workflow/` project
(`backend/**`, `frontend/src/**`, and the project's folder layout). This includes the three quiz
workflows — `classroom_quiz`, `mcq_practice` (`backend/agent/practice.py`), and `module_quiz`
(`backend/agent/module.py`, prompts `18_module_plan`/`19_module_generate`) — which deliberately share
`nodes.py`/`rubric.py`/`variants.py` helpers; when flagging duplication across them, prefer extracting
a shared helper over collapsing a workflow.

## Procedure

### 1. Detect dead & unused code
Prefer real analyzers; fall back to grep-based reference counting if they aren't installed
(see `REFERENCE.md` for exact commands and fallbacks). Never hard-require a tool — degrade gracefully.

- **Python** (`backend/**`):
  - `ruff check` for unused imports (F401), redefinitions (F811), unused variables (F841), etc.
  - `vulture` for unused functions/classes/attributes (treat as *candidates*, verify each).
  - Fallback: `Grep` each defined symbol across the project; zero non-definition hits ⇒ candidate.
- **JS / React** (`frontend/src/**`):
  - `npx knip` (unused files/exports/deps) and/or `eslint` if configured.
  - Fallback: `Grep` each exported component/function across `src/`.
- **Orphan files & folders**: files with no inbound imports/references; empty or stale directories;
  check generated/output folders before suggesting removal.

Verify every automated "unused" hit by hand — dynamic imports, string-based references, framework
entry points (Flask routes, React route elements, LangGraph node registries) can hide real usage.

### 2. Assess maintainability
Flag, with `file:line`:
- Functions that are too long or do too many things.
- Duplicated logic that could be shared.
- Unclear names, magic numbers, missing docstrings/comments where intent isn't obvious.
- Spots where a simpler, more beginner-friendly approach exists — include a short rewrite sketch.

Match the surrounding code's style and conventions; don't impose a new paradigm.

### 3. Report (grouped)
Produce three clearly separated buckets:
- **(A) Safe deletions** — confirmed dead code, unused imports, orphan files. Each with evidence.
- **(B) Refactor suggestions** — beginner-friendly rewrites with before/after sketches.
- **(C) Needs review** — anything risky or ambiguous (possible dynamic usage, public API, behavior
  change). Never auto-delete these.
End with a one-line maintainability summary and the count in each bucket.

### 4. Apply ONLY after approval
After the user confirms which buckets/items to apply:
- Use `Edit` to remove dead code and apply approved refactors, **preserving behavior**.
- Never delete something whose described purpose contradicts what you actually find — surface the
  conflict instead of proceeding.
- After editing, re-run the relevant analyzer / a quick import check and report what changed.

## Output format
```
## Optimization report (scope: <path>)
Maintainability: <one-line summary>

### A. Safe deletions (N)
- backend/...:LINE — <symbol/file> unused (evidence: <ruff F401 | 0 refs | knip>)

### B. Refactor suggestions (N)
- backend/...:LINE — <issue>; suggested simpler form:
  ```<lang>
  <short sketch>
  ```

### C. Needs review (N)
- frontend/...:LINE — <why ambiguous>

Reply with which items to apply (e.g. "apply A", "apply A + B1,B3").
```

See `REFERENCE.md` for tool-detection commands, fallbacks, safe-to-delete heuristics, and refactor patterns.
