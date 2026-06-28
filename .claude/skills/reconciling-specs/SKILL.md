---
name: reconciling-specs
description: Reconciles the project's planning docs (.claude/specs/ and .claude/plan/) against the ACTUAL implementation so the docs accurately describe the app. Cross-references every documented claim with the real backend/frontend code, classifies each as matches / drifted / not-implemented / explicitly-future, reports a drift table, and updates the spec & plan files ONLY after the user approves. Preserves clearly-labelled future scope. Use when the user says "reconcile specs/plan with the implementation", "update the specs/plans to match the code", "remove specs that aren't in the app", "check for spec drift", or "make the docs reflect what's actually built".
---

# Reconciling specs & plans with the implementation

Keep `.claude/specs/` and `.claude/plan/` honest: they should describe what the application
**actually does**. Remove things documented but never built, fix descriptions that drifted from the
code, and **preserve** scope that is clearly marked as future. **Report first, edit only after approval.**

## When this runs

Trigger on requests to reconcile/align specs or plans with the implementation, remove
documented-but-absent features, or check for spec drift. Default scope: this project's
`.claude/specs/*.md` and `.claude/plan/*.md` vs `backend/**` and `frontend/src/**`.

## Procedure

### 1. Read the docs
- All spec files: `.claude/specs/00-…` through `09-…`.
- All plan files: `.claude/plan/feature-01-…` through `feature-09-…`.
Note each concrete claim (a node, prompt, endpoint, model, page, behavior, count, contract).

### 2. Cross-reference each claim against the implementation
Use the mapping table in `REFERENCE.md`. Verify against real code, not memory:
- Workflow nodes & gates → `backend/agent/graph.py`, `nodes.py`, `rubric.py`, `variants.py`, plus `practice.py` (`mcq_practice`) and `module.py` (`module_quiz`). Three workflows fork at `_route_after_assemble`.
- Prompts → `backend/agent/prompts/01…13`.
- Data models / scoring / rubric → `backend/domain/` (`models.py`, `state.py`, `scoring.py`, `rubric_seed.py`).
- API endpoints → `backend/api/` (`app.py`, `agent.py`, `content.py`, `rubric.py`).
- React pages/components/hooks → `frontend/src/`.
Confirm specifics: node names, prompt count/order, variant-type count, endpoint paths, gate count, model field names.

### 3. Classify each claim
- ✅ **matches** — doc agrees with code. Leave as-is.
- ⚠️ **drifted** — doc describes something different from what the code does (wrong name, count,
  behavior, shape). Needs a correction.
- ❌ **not implemented** — documented but absent from the code, and **not** marked as future.
  Candidate for removal/relocation.
- 🔭 **explicitly future** — labelled as planned/future/roadmap. NOTE: **MCQ Practice** (Feature 8) and **Module Quiz** (Feature 9) are now **BUILT**, not future — treat docs that still call them "future scope" as ⚠️ drifted.
  **Preserve.** Do not delete documented future scope; at most tidy its labelling.

### 4. Report the drift table
```
| Doc file : section | Claim | Status | Required change |
|---|---|---|---|
| specs/05-…:§4 | "8 variant types" | ✅ | none |
| plan/feature-04-…:§Gates | "Gate at X" | ⚠️ | code does Y → reword |
| specs/0X-…:§Z | "<feature>" | ❌ | not in code → remove/relocate |
| specs/00-…:§E | "Module Quiz" | 🔭 | keep (future) |
```
Summarize counts per status. Stop here and ask which corrections to apply.

### 5. Apply ONLY after approval
After the user confirms:
- Edit the affected spec/plan `.md` files so they reflect reality: remove or relocate ❌ items,
  reword ⚠️ items to match the code, keep 🔭 future scope intact and clearly labelled.
- Edit **only** files under `.claude/specs/` and `.claude/plan/` — never change implementation code.
- Preserve each doc's existing structure, heading style, and numbering; make minimal targeted edits.
- Report a summary of what changed per file.

## Guardrails
- Implementation is the source of truth for *what is built*; do not "fix" code to match a doc.
- Never delete a section just because it's aspirational — only remove claims that present
  non-existent functionality **as if already built**.
- If a doc and the code genuinely disagree on intent, surface it as a question rather than guessing.

See `REFERENCE.md` for the spec/plan → implementation mapping table and the classification legend.
