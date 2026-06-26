# 03 — Content Ingestion & Session Memory (as-built)

> How Markdown course content becomes **session-keyed memory**, the memory structures, and the feedback→rubric learning loop. The memory layer is LangGraph `PostgresStore` (`02 §4`). Module-quiz multi-session assembly is **future scope** (§Future).

## 0. The memory structures

Memory (LangGraph `PostgresStore`, `02 §4`) holds:

| # | Structure | Namespace | What it is | Read by | Written by |
|---|---|---|---|---|---|
| 1 | **Session content** | `("content", course, session)` | the ingested reading material, chunked (embedding optional) | (search/QA) | ingestion |
| 2 | **Session source + outcomes** | `("source", …)`, `("outcomes", …)` | the **exact full Markdown** + derived learning outcomes | `assemble` (loads full source — never sampled) | ingestion |
| 3 | **Rubric** (one global) | `("rubric_checkpoints",)`, `("rubric_config",)` | the 35 checkpoints (30 base + 5 code-scoped) + per-category min points, seeded from `backend/domain/rubric_seed.py` | `rubric_score`/`variants_score` (`load_rubric`) | seed on boot · feedback promotion |
| 4 | **Feedback** | `("feedback",)` | short authoring rules distilled from human rejections (category-tagged; embedded; `hit_count`+`aliases`, never deleted) | generation/optimization prompts (top-k or semantically relevant per `feedback_retrieval_mode`) | the gates (`05`) |

Plus per-run telemetry: `("provenance", run_id)` (every LLM call) and `("run_cost", run_id)` (exact spend). Generated questions are **exported, never stored in memory**. A concrete reject → rule → checkpoint-promotion demo is in `06 §7`.

## 1. Ingestion pipeline (`backend/ingestion/`)

As built, ingestion is **Markdown-tree based**:
```
reading_materials/<course>/<file>.md
   → chunk_markdown (heading-aware)  → ("content", course, session) chunks
   → extract_title                   → session_title
   → derive_outcomes                 → ("outcomes", course, session)
   → (full file)                     → ("source", course, session)   — the exact text assemble loads
```

### 1.1 Parse + chunk (`ingestion/parse.py`)
- **`chunk_markdown(text, target=chunk_target, max=chunk_max, overlap=chunk_overlap)`** — heading-aware greedy packing (split at `#`/`##` boundaries or when the next block would exceed `chunk_max`); **never splits inside a fenced code block** (rubric 1.10/4.3 need full code). Targets ≈400 tokens, max ≈550, overlap ≈60 (all in `settings.py`).
- **`extract_title(text)`** → the session's human title from the first heading. **`slugify(name)`** → the `(course, session)` slug from the directory/filename. **`derive_outcomes(text)`** → the must-cover learning outcomes from the heading structure (used by `concept_check`).
- Chunks are stored via `memory.put_chunk(...)` — **idempotent** (keyed by `content_hash`; returns `False` if already present). Embeddings are **optional** and off by default for speed (assemble uses the full source text, not vector search).

### 1.2 Curriculum enrichment (`ingestion/curriculum.py`, optional)
`parse_curriculum(xlsx)` (openpyxl) maps session slugs → official `session_title` + `module`. **Enrichment only** — md ingest must succeed even if the xlsx is absent or fails; a tolerant slugifier maps titles → folder slugs.

### 1.3 Bulk CLI (`ingestion/cli.py`)
```bash
python -m backend.ingestion.cli --tree reading_materials/ \
  [--curriculum Gen-AI-Course-Curriculum.xlsx] [--dry-run] [--skip-glob '*code-reference*,*packages*']
```
Walks `reading_materials/<course>/<file>.md`, derives `course` from the directory and `session` from the filename, joins curriculum for title/module. On first run it also calls `seed_rubric_if_empty()` to load the checkpoints into memory (`ensure_rubric_checkpoints()` backfills newer ids such as the Feature 7 `6.x`).

### 1.4 Upload API (`api/content.py`) — contracts in `07`
- `POST /api/content/upload` — upload a `.md` file or pasted Markdown for a `(course, session)`; runs `chunk_markdown` + `put_chunk` (embed off by default).
- `GET /api/content/courses` → list courses. `GET /api/content/sessions?course=` → `[{session, session_title, module, …}]` (the picker). `GET /api/content/session?course=&session=` → the full source + outcomes. **Selecting a session in the UI is what `assemble` loads at run start** — there is no separate "load" step.

## 2. What `assemble` reads
`assemble` loads the session's **exact full Markdown** from `("source", course, session)` and its ordered sections + outcomes — the questions are grounded in the **whole** session text (never a sampled top-k). The critic later receives the same source as ground truth plus the **rubric checkpoints** for the scope and the **top feedback rules**.

## 3. The feedback → rubric learning loop (by category)

- **No stored generated questions** — they are exported only.
- **Reject → category feedback rule.** A rejection at any gate (reasons + free text, **mandatory**) is distilled by an LLM into **one** generic, reusable authoring rule (prompt 06 at Gate 1 via `feedback.distill_and_persist`; prompt 10 at Gates 2/3 via `rubric._handle_rejection`), **tagged with the failed checkpoint's category**, and stored in `("feedback",)`. **Non-destructive, scalable dedup:** an exact repeat bumps `hit_count`; in semantic/hybrid mode a *paraphrase* of an existing lesson (cosine ≥ `feedback_dedup_similarity`) **evolves that lesson in place** — bumps it and records the new wording in `aliases` — instead of creating a near-duplicate row. **Nothing is ever deleted.** Injection: top-`hit_count` rules for generation; **semantically relevant to the current failure reasons** for refine/optimize/improve when `feedback_retrieval_mode` is `"semantic"`/`"hybrid"` (default `"frequency"` = today's top-k). One-time `memory_admin backfill` embeds rules; `memory_admin fold` merges existing duplicates onto a canonical via a `superseded_by` flag (still stored, skipped at read). See `memory-and-feedback-explained.md` §Scalability.
- **Recurring → checkpoint promotion.** When a rule's `hit_count ≥ settings.rubric_promote_threshold` (default 3), `memory.promote_checkpoint_from_feedback(...)` sharpens that checkpoint's `met_when` **in the same category** (never crosses categories). Written straight to `("rubric_checkpoints",)` — no file, no reload. (`04 §7`, `06 §7`.)

## Future scope — module-quiz multi-session assembly

For `module_quiz` (`00 §E`), a new assemble step would merge **2–3 sessions**:
1. fetch each session's source/chunks; 2. balance a per-session question budget; 3. cross-session dedup (cosine on stored vectors, no new embeds); 4. concatenate into one grounded context with `## Session: <title>` breadcrumbs; 5. record per-question `source_label`. The rest of the pipeline (split-or-pool → generate → rubric → variants → export) is reused. Not built today.

## Definition of Done
- [ ] `.md` ingest → `("content"/"source"/"outcomes", course, session)` keyed by `(course, session)` + title (idempotent); code blocks never split.
- [ ] `GET /api/content/sessions` lists sessions; selecting one is what `assemble` loads (full source).
- [ ] The rubric self-seeds via `seed_rubric_if_empty()` on first ingest/boot.
- [ ] Memory holds session content/source/outcomes + the global rubric + feedback (by category) — no gold table, no stored generated questions.
- [ ] reject→category-feedback and feedback→checkpoint-promotion both work within-category (`04 §7`).
