# 08 — Infrastructure & Deployment (as-built)

> Environment, Postgres (Neon), local dev, and serving (SSE-aware). Settings load via `backend/settings.py` (pydantic-settings) from `agentic-mcq-generation-workflow/.env`.

## 1. Environment variables (`.env`)

| Var | Required | Purpose | Default |
|---|---|---|---|
| `POSTGRES_STORE_DSN` | ✅ | the memory layer (LangGraph `PostgresStore`: content, source, outcomes, rubric, feedback, provenance, run_cost) | — |
| `AGENT_STORE_DSN` | ⬜ | operational tables (`agent_runs`, `agent_step_events`) | falls back to `POSTGRES_STORE_DSN` |
| `LANGGRAPH_CHECKPOINT_DSN` | ⬜ | graph checkpoints (`PostgresSaver`) | falls back to `POSTGRES_STORE_DSN` |
| `OPENROUTER_API_KEY` | ✅ | LLM (generation/critic) | — |
| `OPENROUTER_MODEL` | ⬜ | the model | `anthropic/claude-haiku-4-5` |
| `OPENROUTER_BASE_URL` | ⬜ | OpenRouter endpoint | `https://openrouter.ai/api/v1` |
| `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` / `EMBEDDING_DIMS` | ⬜ | embeddings (optional; chunks stored without vectors by default) | `…/v1` · `openai/text-embedding-3-small` · `1536` |
| `CHUNK_TARGET` / `CHUNK_MAX` / `CHUNK_OVERLAP` | ⬜ | chunking | `400` / `550` / `60` |
| `GENERATED_QUIZZES_DIR` | ⬜ | export root | `./generated_quizzes` (rel. to `.env`) |
| `LLM_MAX_CONCURRENCY` | ⬜ | `pmap` thread-pool size | `6` |
| `CRITIC_BATCH_SIZE` | ⬜ | questions per rubric/variant critic call | `8` |
| `PRICE_INPUT_PER_M` / `PRICE_OUTPUT_PER_M` | ⬜ | Haiku list price (the $ token estimate) | `1.0` / `5.0` |
| `USD_TO_INR` | ⬜ | ₹ display rate | `83.5` |
| `RUBRIC_PROMOTE_THRESHOLD` | ⬜ | rule hit_count before a checkpoint is promoted | `3` |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` | ⬜ | optional tracing | `false` / — / `agentic-mcq-workflow` |

Neon/managed Postgres: the DSNs may all point to the same database. The three pools (store, checkpointer, event-writer) all set `check=ConnectionPool.check_connection` + `max_idle=120` so connections Neon drops after idle are transparently replaced.

### LangSmith block (paste the key here)
In `agentic-mcq-generation-workflow/.env` (same file as `OPENROUTER_API_KEY`):
```
# ── Observability (LangSmith) — optional ──
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...        # ← from smith.langchain.com → Settings → API Keys
LANGSMITH_PROJECT=agentic-mcq-workflow
```
`observability.init_tracing()` exports the `LANGCHAIN_*` env vars at startup; leave the key blank / tracing false to disable (zero overhead).

## 2. Postgres
`memory.app_store()` calls `PostgresStore.setup()`; `graph` calls `PostgresSaver.setup()`; `storage.ensure_schema()` creates `agent_runs` + `agent_step_events`. pgvector is only needed if embeddings are enabled (off by default — assemble uses the full source text, not vector search):
```sql
CREATE EXTENSION IF NOT EXISTS vector;   -- only if EMBEDDING_* is configured
```

## 3. Dependencies
Backend: `langgraph`, `langchain-openai`, `langgraph-checkpoint-postgres`, `langgraph` store (`PostgresStore`), `psycopg[binary]`, `psycopg_pool`, `pydantic>=2`, `pydantic-settings`, `flask`, `flask-cors`, `openpyxl` (curriculum xlsx only), `langsmith` (optional tracing), `httpx`. Frontend: `react`, `react-router-dom`, `vite`.

## 4. Local development
```bash
# 0. env
cp .env.example .env            # fill POSTGRES_STORE_DSN + OPENROUTER_API_KEY

# 1. ingest course content (also seeds the rubric on first run)
python -m backend.ingestion.cli --tree reading_materials/ \
       [--curriculum Gen-AI-Course-Curriculum.xlsx] [--dry-run]

# 2. servers
python -m flask --app backend.api.app run --port 5001     # API
cd frontend && npm install && npm run dev                 # Vite :5173 (proxies /api → :5001)
```
Open `http://localhost:5173`, pick a course + session, click Generate.

## 5. Production
- **Gunicorn** (threaded for SSE + the per-run driver threads): `gunicorn -w 1 --threads 32 --worker-class gthread --timeout 0 backend.api.app:app --bind 0.0.0.0:5001`. A single worker keeps the in-process `RunBus` + run-driver threads coherent (multi-worker would need a shared pub/sub — out of scope).
- **Nginx for SSE:** `location /api/agent/stream/ { proxy_pass http://localhost:5001; proxy_buffering off; proxy_read_timeout 1h; }`.
- **Frontend:** `npm run build`; serve the static bundle; point it at the API base.
- **Resilience:** on restart, `warm_agent()` runs `init_tracing()` + `reconcile_stalled()` (orphaned `running` → `stalled`) so the UI never shows a phantom live run.
- **Secrets:** `.env` only; never commit; the OpenRouter key stays server-side (cost is proxied).

## 6. Scaling
Single-process (in-memory `RunBus` + run-driver threads). Bounded by `LLM_MAX_CONCURRENCY` (in-node) and one thread per run. Horizontal scaling would require moving SSE pub/sub to Redis/Postgres LISTEN-NOTIFY — a documented future step.

## Definition of Done
- [ ] `.env.example` lists §1; settings load and fail-fast on a missing `POSTGRES_STORE_DSN`/`OPENROUTER_API_KEY`.
- [ ] On boot: store + checkpointer + `agent_runs`/`agent_step_events` schemas exist; the rubric self-seeds; `reconcile_stalled()` runs; all pools survive Neon idle drops.
- [ ] Local dev: ingest succeeds, API + Vite run, a classroom run completes from the browser.
- [ ] SSE serves correctly under gunicorn + nginx (`proxy_buffering off`); LangSmith traces when enabled.
