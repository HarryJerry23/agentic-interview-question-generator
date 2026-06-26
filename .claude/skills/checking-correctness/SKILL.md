---
name: checking-correctness
description: Checks whether this project's code is correct and up to date with the LATEST official documentation of every library it uses (LangGraph, LangChain, Flask, psycopg, pydantic-settings, React, Vite, etc.). Fetches current docs via the Context7 and LangChain documentation MCP tools plus web search, compares actual usage against them, and produces a conformance score out of 10 with a prioritized fix list. Use when the user says "check correctness", "is the code up to date", "verify against latest docs", "check the syntax / API against the latest version", "are we using deprecated APIs", or asks for a version/API conformance check.
---

# Checking correctness & doc-freshness

Verify that the code in this project conforms to the **latest official documentation** of the
libraries it depends on, then report a **score out of 10**. This skill is **read-and-report only** —
it never edits code unless the user explicitly asks afterward.

## When this runs

Trigger on any request to confirm the code is correct / current / not using deprecated APIs, or to
"check syntax/implementation against the latest docs". Default scope: the
`agentic-mcq-generation-workflow/` project (`backend/`, `frontend/`).

## Procedure

### 1. Inventory the real dependencies
- Read `requirements.txt` and `frontend/package.json` to get declared libraries + pinned versions.
- Use `Grep` to confirm which are **actually imported** in `backend/**` and `frontend/src/**`.
  Only check libraries that are genuinely used — skip unused pins (note them as a minor finding).
- Produce a short table: library → pinned version → where used (key files).

### 2. Fetch the latest documentation for each library
Route each library to the best source (see `REFERENCE.md` for the full routing table):
- **LangChain / LangGraph / langchain-openai / langgraph-checkpoint-postgres** →
  use the LangChain docs MCP first: `mcp__docs-langchain__search_docs_by_lang_chain` then
  `mcp__docs-langchain__query_docs_filesystem_docs_by_lang_chain`.
- **Everything else** (Flask, psycopg, pydantic-settings, tiktoken, React, Vite, react-router,
  @xyflow/react, react-markdown) → use Context7:
  `mcp__plugin_context7_context7__resolve-library-id` then `mcp__plugin_context7_context7__query-docs`.
- **Fallback / "what is the newest version" / release-notes / deprecation timelines** →
  `WebSearch` + `WebFetch` against the official docs site.

Always fetch docs even for libraries you think you know — training data may be stale. Ask the doc
source targeted questions (e.g. "PostgresStore setup latest API", "Flask 3 app factory", "pydantic-settings v2 BaseSettings import path").

### 3. Run the conformance check
For each used subsystem, compare actual code against the latest docs and record concrete findings:
- **Imports / deprecations** — moved or renamed import paths, deprecated symbols, removed aliases.
- **API signatures** — changed/renamed/removed function & method parameters, return shapes.
- **Recommended patterns** — superseded idioms (e.g. LangGraph checkpointer/store construction,
  `interrupt`/resume, Flask 3 patterns, pydantic-settings v2 config, React 18 hook idioms).
- **Version currency** — pinned version vs latest stable; flag majors behind.
- **Type / contract correctness** — Pydantic model usage, typed state, etc.

Each finding must cite `file:line`, the outdated usage, the current-docs replacement, and a doc URL/citation.

### 4. Score it /10
Apply the weighted rubric in `REFERENCE.md`. Report:
- **Overall: N/10**
- **Per-category subscores** (Imports/deprecations, API signatures, Patterns, Version currency, Types/contracts).

### 5. Report the path to 10/10
If the score is below 10/10, output a **prioritized "To reach 10/10" list** ordered by severity:
each item = `file:line` · what's outdated · the current-docs fix · citation. Group by library.
Do **not** edit anything. End by offering: "Want me to apply these fixes?" — only edit if the user says yes.

## Output format
1. Dependency inventory table.
2. Findings grouped by library (with citations).
3. Scorecard: overall N/10 + per-category subscores.
4. "To reach 10/10" prioritized fix list (omit if already 10/10).

See `REFERENCE.md` for the scoring rubric, doc-source routing table, and an example report.
