# optimizing-code — reference

## Tool detection & commands

Check availability first; if a tool is missing, mention the install command once and fall back to grep.

### Python (`backend/`)
```bash
# Unused imports / vars / redefinitions (fast, low false positives)
ruff check backend/ --select F401,F811,F841,F --output-format concise
# or, if ruff isn't installed:  python -m pyflakes backend/

# Unused functions/classes/attributes (CANDIDATES — verify each)
vulture backend/ --min-confidence 80
# install if missing:  pip install vulture ruff
```
Grep fallback for a suspected-unused symbol `foo`:
```bash
rg -n '\bfoo\b' backend/   # 1 hit (the definition) ⇒ candidate for removal
```

### JS / React (`frontend/`)
```bash
npx --yes knip            # unused files, exports, dependencies (run from frontend/)
npx eslint src/           # if an eslint config exists
```
Grep fallback for an exported component `Foo`:
```bash
rg -n '\bFoo\b' frontend/src/   # only the definition/export ⇒ candidate
```

### Orphan files / empty dirs
```bash
# empty directories
find backend frontend/src -type d -empty
# a file with no inbound imports — grep its module name across the tree
rg -n "from .*<modulename>|import .*<modulename>|<componentname>" .
```

## Safe-to-delete vs needs-review heuristics

**Likely safe (bucket A)** — still verify:
- Imports flagged F401 by ruff/pyflakes.
- Local helper functions/classes with exactly one definition and zero other references.
- Files in the tree that nothing imports AND aren't entry points or generated output.

**Needs review (bucket C) — never auto-delete:**
- Anything referenced dynamically: `getattr`, string keys, registries, decorators.
- Flask route handlers, LangGraph node functions wired into the graph, React components used as
  route `element`s — these are referenced indirectly.
- Public-looking exports, `__init__.py` re-exports, `__all__` entries.
- Prompt files (`backend/agent/prompts/*.md`) and content/output dirs (`reading_materials/`,
  `generated_quizzes/`) — loaded by path, not import.
- `.env.example`, config, fixtures, anything a human might rely on out-of-band.

When in doubt, put it in C and explain the uncertainty.

## Beginner-friendly refactor patterns

- **Extract a well-named function** from a long block instead of a comment explaining it.
- **Replace magic numbers/strings** with named constants near the top of the module.
- **Early return / guard clauses** instead of deep nesting.
- **Name for intent** (`accepted_questions` not `aq`); rename only where it doesn't break a public contract.
- **Add a one-line docstring** stating what a function does + its inputs/outputs when not obvious.
- **De-duplicate** repeated logic into a shared helper — but only if the duplicates are truly the same intent.

Keep diffs small and behavior identical. Prefer several tiny, reviewable edits over one large rewrite.
