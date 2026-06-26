# Feature 1 — Data Ingestion: Reading Materials + Rubric into LangGraph Memory (PostgresStore)

## Context

`agentic-mcq-generation-workflow/` is a clean, spec-driven rebuild of the MCQ-generation system.
Before any generation can happen, the system's **memory** must be populated. This first feature
loads the current data into Postgres, organized course-wise, so a future UI dropdown can pick a
course → session and a quiz run can load that session's content + the rubric.

**Key decision (confirmed): use the LangGraph long-term-memory Store as the single memory layer.**
Ingestion writes through `langgraph.store.postgres.PostgresStore` so the **future LangGraph agent
reads it natively** — nodes call `runtime.store.search(...)` after `graph.compile(store=store)`,
with zero custom glue. This is the official injection pattern (verified against the LangChain docs),
and it's *simpler* than hand-rolling tables: `store.setup()` manages the vector tables and `put`
embeds automatically. (This intentionally supersedes spec `02`'s custom `course_content` table; the
spec stays the behavioral reference for chunk sizes, the rubric, and parsing rules.)

**Store API used (Python, verified):**
```python
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import IndexConfig
with PostgresStore.from_conn_string(STORE_DSN, index=IndexConfig(embed=embeddings, dims=1536)) as store:
    store.setup()                                                  # creates/maintains vector tables
    store.put(("content", course, session), key, {"text": ...}, index=["text"])   # auto-embeds "text"
    store.put(("rubric",), cid, {...}, index=False)                # stored, not embedded
    store.get(ns, key)                                             # idempotency check
    store.search(("content", course, session), query=..., limit=k) # semantic; no query = list all
    store.list_namespaces(prefix=("content",), max_depth=3)        # → course→session dropdown
```
- `store.search` with **no query** lists everything under a namespace prefix (used for full-session load).
- `PostgresStore` orders `search` results by `updated_at` desc → we sort client-side by `chunk_index`.
- One embedding model per store (`text-embedding-3-small`, dims 1536).

## Namespace plan

| Memory | Namespace | Key | Value | Embedded? |
|---|---|---|---|---|
| Reading-material chunks | `("content", course, session)` | `content_hash` | `{text, heading_path, session_title, module, chunk_index}` | `index=["text"]` |
| Session outcomes | `("outcomes", course, session)` | `"_"` | `{session_title, module, outcomes[], confidence}` | `index=False` |
| Rubric checkpoints (30) | `("rubric_checkpoints",)` | checkpoint id (`"1.1"`) | full `Checkpoint` dict | `index=False` |
| Rubric config (per-cat mins) | `("rubric_config",)` | `f"{scope}:{category}"` | `{scope, category, min_points}` | `index=False` |
| Feedback rules | `("feedback", category)` | `rule_id` | rule dict | created empty (later feature) |

> **Implementation note — namespace prefix matching.** `PostgresStore.search(prefix)` matches by
> *character* prefix of the dot-joined namespace path, not element-wise. So `("rubric",)` would also
> match `("rubric_config",)`, and `("content", c, "mastering_image_generation")` would absorb
> `..._with_stable_diffusion`. Mitigations in `memory.py`: (1) the rubric namespace is
> `("rubric_checkpoints",)` (non-prefixing with `("rubric_config",)`); (2) every namespace-scoped read
> filters to the exact namespace via `_only(items, ns)`.

Dropdown: `list_namespaces(prefix=("content",), max_depth=2)` → courses; `max_depth=3` → sessions;
session title/module read from the matching `("outcomes", …)` item.

## Source data

- `agentic-mcq-generation-workflow/reading_materials/<course>/<file>.md` — 3 courses, 77 `.md`
  (`building_llm_applications` 26, `introduction_to_ai_for_finance` 26, `introduction_to_generative_ai` 25).
- `Gen-AI-Course-Curriculum.xlsx` — optional enrichment (titles/modules/outcomes); ingest must succeed without it.
- `backend/domain/rubric_seed.py` — 30 `Checkpoint`s + `CATEGORY_MIN` (reused as-is for seeding).

Mapping: `course` = directory; `session` = filename stem; `session_title` = first H1 else humanized filename;
`module`/`outcomes` from curriculum if matched, else outcomes derived from heading leaves.

## Target structure (simple — 2 packages + 2 infra modules)

```
agentic-mcq-generation-workflow/
  .env                          NEW — STORE_DSN + embedding key/model (own, separate from parent)
  .env.example                  NEW — template
  requirements.txt              NEW
  backend/
    settings.py                 NEW — loads THIS folder's .env; STORE_DSN, embedding + chunk params
    memory.py                   NEW — the memory layer: open_store() (PostgresStore + IndexConfig),
                                      put_chunk/get_session/list_courses/list_sessions,
                                      put_outcomes, seed_rubric_if_empty/load_rubric
    domain/
      rubric_seed.py            EXISTS — 30 checkpoints, reused
      scoring.py                MOVED from backend/eval/scoring.py (pure; eval/ removed)
    ingestion/
      parse.py                  NEW — markdown -> heading-aware chunks (extract+chunk; code fences whole)
      curriculum.py             NEW — parse_curriculum(xlsx) (tolerant; enrichment only)
      cli.py                    NEW — bulk ingest entry point
```

> No `db.py`, no embed module, no custom DDL — `PostgresStore` owns connections, schema, and
> embedding. Embedding is configured once in `memory.open_store()` via `IndexConfig`.

## Implementation steps

1. **First action:** copy this approved plan into `agentic-mcq-generation-workflow/.claude/plan/`.
2. `requirements.txt`: `langgraph`, `langgraph-checkpoint-postgres` (PostgresStore), `langchain`,
   `langchain-openai` (embeddings), `psycopg[binary]`, `tiktoken`, `openpyxl`, `pydantic-settings`,
   `python-dotenv`. (Postgres needs the `vector` extension; `store.setup()` creates the rest.)
3. `.env.example` + `.env` in the workflow folder: `POSTGRES_STORE_DSN`, `EMBEDDING_MODEL`
   (`text-embedding-3-small`), `EMBEDDING_API_KEY` + `EMBEDDING_BASE_URL` (OpenAI-compatible),
   plus `OPENROUTER_API_KEY` / `AGENT_STORE_DSN` / `LANGGRAPH_CHECKPOINT_DSN` as placeholders for
   later features. Point DSN at a fresh/separate database.
4. `backend/settings.py`: `pydantic-settings` `BaseSettings`, `env_file = Path(__file__).parents[1] / ".env"`;
   exposes `POSTGRES_STORE_DSN`, embedding config, chunk params (`CHUNK_TARGET=400`, `MAX=550`, `OVERLAP=60`).
5. `backend/memory.py`:
   - `open_store()` → context manager building `PostgresStore.from_conn_string(STORE_DSN,
     index=IndexConfig(embed=OpenAIEmbeddings(model=…, base_url=…, api_key=…), dims=1536))`;
     calls `store.setup()` and `CREATE EXTENSION IF NOT EXISTS vector` if needed.
   - `put_chunk(store, course, session, chunk)`: key = `sha256(course|session|text)`; **`store.get`
     first and skip if unchanged** (idempotent + avoids re-embedding); else `store.put(("content",
     course, session), key, {...}, index=["text"])`.
   - `put_outcomes(store, course, session, …)`, `get_session(store, course, session)` (search no-query,
     sort by `chunk_index`), `list_courses(store)` / `list_sessions(store, course)` via `list_namespaces`.
   - `seed_rubric_if_empty(store)`: if `("rubric",)` empty, `put` all 30 `CHECKPOINTS` + `CATEGORY_MIN`
     rows (`index=False`). `load_rubric(store)`: read them back.
6. Move `backend/eval/scoring.py` → `backend/domain/scoring.py`; update its import path; delete empty `eval/`.
7. `ingestion/parse.py`: split `.md` on ATX headings (`#`..`####`), carry `heading_path`, keep fenced
   code / `<details>` intact; heading-aware greedy packing ~400 tokens (`tiktoken cl100k_base`), max 550,
   overlap 60; never split inside a code fence (emit oversized chunk). Returns `Chunk(text, chunk_index,
   heading_path, token_count)`.
8. `ingestion/curriculum.py`: `parse_curriculum(xlsx)` with `openpyxl(data_only=True)`; tolerant
   slugifier mapping titles → folder slugs; `{(course,session): (title, module, outcomes)}`; never fatal.
9. `ingestion/cli.py`: `python -m backend.ingestion.cli --tree reading_materials/
   [--curriculum Gen-AI-Course-Curriculum.xlsx] [--dry-run] [--skip-glob '*code-reference*,*packages*']`.
   Opens the store, `seed_rubric_if_empty()`, walks the tree, derives course/session, parses → chunks,
   `put_chunk` each, `put_outcomes` per session (from curriculum else derived). `--dry-run` prints counts only.

## Verification (end-to-end)

1. **Dry run:** `python -m backend.ingestion.cli --tree reading_materials/ --dry-run` → 3 courses,
   ~77 sessions, total chunk count; writes nothing.
2. **Real ingest**, then a small Python check using `memory.open_store()`:
   - `list_courses(store)` → the 3 courses; `list_sessions(store, "building_llm_applications")` → its
     sessions with titles.
   - `len(get_session(store, "building_llm_applications", "<a-session>"))` > 0 and chunks sorted by `chunk_index`.
   - `store.search(("content","introduction_to_generative_ai"), query="prompt engineering", limit=3)`
     returns relevant chunks (confirms embeddings populated + semantic search works).
   - `load_rubric(store)` → 30 checkpoints + the `CATEGORY_MIN` config.
3. **Store tables exist:** `psql "$POSTGRES_STORE_DSN" -c "\dt"` shows the PostgresStore tables (`store`,
   vector table); a `count(*)` on the store table ≈ chunks + 77 outcomes + 30 rubric + config rows.
4. **Idempotency:** run the ingest twice — second run re-embeds ~0 chunks (hash skip), counts unchanged.
5. **Existing self-tests still pass:** `python -m backend.domain.rubric_seed` (30 checkpoints) and
   `python -m backend.domain.scoring` (green/red, after the move).

## Out of scope (later features)

- **Feature 2:** Flask `content` API + React shell with the course→session dropdown (built on
  `list_courses`/`list_sessions`/`get_session`) as its first page.
- The LangGraph generation/eval graph (will `compile(store=store)` and read via `runtime.store`),
  `.pptx`/`.pdf` extractors, module-quiz cross-session assembly, `feedback_rules` population, `prompts/`.
