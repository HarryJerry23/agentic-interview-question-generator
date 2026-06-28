# Feature 2 — Content API + React frontend (browse, upload, rubric viewer) — AS BUILT

> **Update — Feature 2.1: UI redesign + Markdown formatting fix (frontend only).**
> - **Formatting fix:** the renderer now uses `remark-gfm` (tables, strikethrough), `rehype-raw`
>   (raw HTML: `<details>`, `<img>`, `<br>`), and `rehype-highlight` + highlight.js github theme
>   (syntax-colored code). Full `.prose` typography in `src/styles/prose.css`. Root cause of the
>   earlier "bad formatting": plain react-markdown rendered no tables / no HTML.
> - **Dashboard/app UI, indigo+slate theme** (`src/styles/theme.css`, Inter font): `TopBar`
>   (logo + Content/Rubric tabs), sticky `Toolbar` card (course/session selects + `+ Upload`),
>   `Article` card (breadcrumb, title, module chip, outcomes disclosure, `Markdown` body), upload
>   in a `Modal`, redesigned `RubricView` (all-required cards + per-category checkpoint cards with
>   good/bad callouts). New components: TopBar, Article, Markdown, Modal, UploadForm; removed Nav,
>   UploadPanel. **No backend/API changes.** Verified via headless-Chrome screenshots (table, code,
>   `<details>`, modal, rubric all render correctly).

## Context

Feature 1 loaded all reading material + the rubric into LangGraph memory (`PostgresStore`).
Feature 2 is the first human-facing surface: a Flask API + Vite/React app to browse that memory.
A user can:
- pick a **course → session** and read the **entire reading material** (rendered Markdown, with a
  title + learning-outcomes header);
- **upload a new session** (file or pasted Markdown) — stored **without embeddings**, **auto-loaded**
  so it appears in the dropdown and is viewable immediately;
- view the **rubric** (30 checkpoints, all required to pass), read-only.

## Layout (inside `agentic-mcq-generation-workflow/`)

```
backend/
  memory.py          put_chunk(embed=…); put_source/get_source; app_store() (pooled singleton);
                     list_sessions() reads the light ("outcomes", course) namespace (perf, see below)
  ingestion/cli.py   stores full source text per session (put_source)
  api/
    app.py           create_app() (Flask + CORS + blueprints + /api/health); warms app_store() at boot;
                     python -m backend.api.app  → :5001
    content.py       /api/content  (courses, sessions, session, upload)
    rubric.py        /api/rubric
requirements.txt     + flask, flask-cors
frontend/            Vite + React + React Router (plain CSS)
  vite.config.js     proxy /api → :5001
  src/lib/api.js
  src/pages/ContentLibrary.jsx   dropdowns + ReactMarkdown viewer + UploadPanel (auto-load)
  src/pages/RubricView.jsx       checkpoints grouped by category (all required)
  src/components/{Nav,Loading,Empty,ErrorState,UploadPanel}.jsx
  src/styles/theme.css
README.md            run instructions
```

## API (JSON; errors `{error, code}`)

| Method & path | Returns |
|---|---|
| `GET /api/health` | `{status:"ok"}` |
| `GET /api/content/courses` | `{courses:[...]}` |
| `GET /api/content/sessions?course=` | `{sessions:[{session, session_title, module}]}` |
| `GET /api/content/session?course=&session=` | `{session_title, module, outcomes:[...], text}` — 404 if unknown |
| `POST /api/content/upload` | multipart `file` **or** JSON `{text}`, + `course`,`session?`,`session_title?` → `{course, session, session_title, chunks, embedded:false}` |
| `GET /api/rubric` | `{category_min:{per_question, per_set}, checkpoints:[...]}` |

Upload: read text → `slugify` session → `extract_title`/`derive_outcomes` (reuse `ingestion/parse.py`)
→ `chunk_markdown` → `put_source` + `put_outcomes` + `put_chunk(embed=False)` per chunk. **No embeddings.**

## Key as-built decisions / fixes

- **`list_sessions` performance.** The first cut did ~2 remote round-trips per session (`get` + `search`)
  → **~45s** over Neon; the dropdown looked broken. A content-scan variant pulled ~180 full-text chunks
  (~3s). Final version reads the **small `("outcomes", course)` namespace** (one tiny row per session) in a
  single query → **sub-second**. Consequence: the dropdown no longer shows a per-session chunk count.
- **Store lifetime.** `app_store()` opens a **pooled** `PostgresStore` once (retains the context-manager so
  the pool isn't GC-closed) and is **warmed at app startup** so the first request isn't a ~6s cold init.
- **Upload without embeddings.** `put_chunk(embed=False)` → `index=False`; chunks + source stored, viewable
  immediately, **not** semantically searchable until embedded later. Verified `store_vectors` count is
  unchanged after an upload.
- **Full-text fidelity.** Each session's original Markdown is stored once under `("source", course, session)`
  (non-embedded) and rendered verbatim — avoids stitching overlapping chunks. Backfilled by re-running the
  Feature 1 CLI (77 source items; chunks skipped, no re-embed).

## How to run

```bash
# from agentic-mcq-generation-workflow/
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill POSTGRES_STORE_DSN + EMBEDDING_API_KEY

# one-time ingest (Feature 1)
export PYTHONPATH=.
python -m backend.ingestion.cli --tree reading_materials/ --curriculum Gen-AI-Course-Curriculum.xlsx

# Terminal 1 — API on :5001
. .venv/bin/activate && export PYTHONPATH=. && python -m backend.api.app
# Terminal 2 — UI on :5173 (proxies /api)
cd frontend && npm install && npm run dev
```
Open http://localhost:5173.

## Verified

- Endpoints: 3 courses, 26/26/25 sessions (titles), session view ~22 KB text + outcomes, rubric 30 + mins.
- Browser (headless CDP): course → 26 sessions populate; session → Markdown renders (title + outcomes header,
  46 headings); no error states.
- Upload (file + paste): `embedded:false`, appears in dropdown immediately, `store_vectors` unchanged.
- `list_sessions` ≈ 0.6–1s warm; first request after boot ≈ 1s (warmed).

## Out of scope (later)

Semantic-search box, embedding uploaded sessions later (re-embed action — data is ready), delete/re-ingest,
rubric editing (`PUT`/reset), feedback views, and the agent/generation/SSE flow (`/api/agent/*`).
