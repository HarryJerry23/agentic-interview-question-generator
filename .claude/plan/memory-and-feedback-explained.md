# How the system learns (memory & feedback)

> What the system remembers, how it learns from a reviewer's corrections, and how that makes the
> next quiz better. Later sections show exactly where this lives in the code and how to check it.

---

## 1. Overview

The system keeps a **notebook of lessons**.

Whenever a human reviewer corrects a question — rejecting it or improving it and saying *why* — the
system writes down a short, general lesson from that correction. Not the specific question, just the
takeaway, for example: *"Make the wrong options believable, not obviously wrong."*

Before it writes the **next** quiz, it reads the most useful lessons from the notebook and keeps them
in mind. So a mistake caught today is less likely to happen tomorrow — even on a completely different
topic. The more often the same lesson comes up, the more weight it carries; and a lesson that keeps
recurring can eventually be promoted into the official quality checklist itself.

Three simple rules govern the notebook:

- **Only general lessons are kept** — never the actual question or course content. A lesson is meant
  to apply anywhere, so it can't contain topic-specific facts.
- **The same lesson is never written twice.** If a lesson comes up again, the system just adds a tally
  mark to the existing one (so it counts as "seen N times") instead of creating a duplicate.
- **Nothing is ever deleted.** Lessons only get stronger or get folded together; the system never
  forgets what it learned.

That's the whole concept. The rest of this guide shows where it's stored and how to inspect it.

---

## 2. Where everything is kept: one table

There is **no separate "feedback table."** Everything the app remembers lives in
**one Postgres table called `store`** (created and managed by LangGraph's
`PostgresStore`). Different *kinds* of memory are separated only by the
**`prefix` column** — which is just the "namespace" written as dotted text.

That is why, in the Neon Tables view, you see thousands of rows that all start
with `content.building_llm_a...` — those are reading-material chunks, the bulk of
the table. The feedback rules are in the *same* table, just under a different
prefix.

### What each `prefix` means

| `prefix` (namespace)                          | What it stores                                  | Embedded? (searchable by meaning) | Rough count |
|-----------------------------------------------|-------------------------------------------------|-----------------------------------|-------------|
| `content.<course>.<session>`                  | reading-material chunks (`{"text": ...}`)       | ✅ yes (`index=["text"]`)         | hundreds    |
| `source.<course>.<session>`                   | full original markdown of a session             | ❌ no                             | 1/session   |
| `outcomes.<course>.<session>`                 | learning outcomes for a session                 | ❌ no                             | 1/session   |
| `rubric_checkpoints`                          | the 30 rubric checkpoints                       | ❌ no                             | 30          |
| `rubric_config`                               | per-category required points (= full count)      | ❌ no                             | a few       |
| **`feedback`**                                | **the learned authoring rules (THE loop)**      | semantic/hybrid mode only         | grows       |
| `run_cost.<run_id>`                           | $/₹ cost of one run                             | ❌ no                             | 1/run       |

> The `checkpoint_writes`, `checkpoints`, `checkpoint_blobs` tables you also saw
> are **NOT memory** — they are LangGraph's internal per-run workflow state (so a
> paused run can resume at a human gate). Ignore them for "memory."

Each row in `store` is: `prefix` (namespace) + `key` + `value` (JSON) +
`created_at` + `updated_at`.

---

## 3. What one lesson looks like

```json
{
  "rule": "Draw distractors from concepts adjacent to the correct answer, never unrelated categories.",
  "hit_count": 3,
  "source": "rubric_gate",          // or "distill" or "human_improve"
  "category": "Correct Answer Validity",  // rubric category, or "" for generation rules
  "checkpoint_ref": "3.1"           // rubric checkpoint id, or "" for generation rules
}
```

Two rules the code strictly enforces:

1. **Only generic rule text is stored** — never the question, never session
   facts. (Enforced by `prompts/06_feedback_distill.md` AND by the code passing
   only *reasons* to the LLM, never content.) That is why a feedback row is tiny.
2. **The `key` is `sha256(normalized rule sentence)`** (`memory.py:_rule_key`).
   So the same lesson learned again does **not** create a duplicate row — it
   **increments `hit_count`** instead. `hit_count` = how many times we've seen
   this lesson = how important it is.

---

## 4. How the system chooses which lessons to use

A setting, `feedback_retrieval_mode`, controls how the lessons are picked before they're given to
the AI:

- **`frequency` (default).** Fetch every feedback row, sort by `hit_count` in
  Python, take the top k (default 8). Plain ranking — no embeddings, cheap and
  deterministic (`memory.py:347` `top_feedback_rules`):

  ```python
  items = _only(store.search(_FEEDBACK_NS, limit=1000), _FEEDBACK_NS)  # NO query arg → list ALL rows
  ranked = sorted(items, key=lambda it: it.value.get("hit_count", 1), reverse=True)
  return [it.value["rule"] for it in ranked[:k]]                       # top-k by hit_count, in Python
  ```

- **`semantic` / `hybrid`.** Rules are embedded and retrieved by **relevance to the
  problem at hand** (the failure reason / reviewer note), blended with `hit_count`.
  This is what makes a rare-but-relevant rule surface instead of staying buried under
  high-frequency ones. Details in §Scalability.

(Content chunks are always embedded — `put_chunk(..., index=["text"])` — and searched
by meaning; feedback rules are embedded only in semantic/hybrid mode.)

---

## 5. The learning loop, step by step

### WRITE side (turning failures into rules) — happens at the *end* of review

| When                                   | Code                                                              | source tag       |
|----------------------------------------|-------------------------------------------------------------------|------------------|
| Concept-check fails + human drop/improve | `nodes.py:418-420` → `feedback.distill_and_persist()`            | `distill`        |
| Reviewer rejects at the rubric gate    | `rubric.py:424 _handle_rejection()` → `put_feedback_rule(...)`    | `rubric_gate`    |
| Reviewer uses the "Improve" box        | `improve.py:92-110`                                               | `human_improve`  |

All three end at **`memory.py:315 put_feedback_rule()`** which dedupes-by-hash and
bumps `hit_count`.

### PROMOTE side (rubric refines itself) — `memory.py:360`

When a `rubric_gate` rule's `hit_count` reaches the threshold
(`settings.rubric_promote_threshold`, default **3**),
`promote_checkpoint_from_feedback()` **appends `" Also: <guidance>"` to that
rubric checkpoint's `met_when` text**. That is the rubric *literally rewriting its
own grading criteria* from repeated human rejections.
- Triggered from `rubric.py:441-442` and `improve.py:108-110`.

### READ side (injecting rules back into prompts) — happens whenever an author step runs

Every injection point calls **one** helper — `rules_block()` (`feedback.py:21`) for the generation
nodes, `_fb_block()` (`rubric.py:105`) for the rubric/variant nodes — and **both call the same brain,
`relevant_feedback_rules()` (`memory.py:477`)**. What that brain does depends on the **query** each
step passes and on `feedback_retrieval_mode`:

| Phase            | Prompt file              | Call (`feedback.py`/`rubric.py`)        | Query passed                          | Basis                |
|------------------|--------------------------|-----------------------------------------|---------------------------------------|----------------------|
| Generate MCQs    | `03_generate_mcq.md`     | `rules_block()`                         | — (none)                              | **frequency**        |
| Refine MCQs      | `05_refine.md`           | `rules_block(query=…)`                   | concept-check *failure reasons*       | **relevance**        |
| Rubric critic    | `07_rubric_critic.md`    | `_fb_block()`                           | — (none — judges all dimensions)      | **frequency**        |
| Rubric optimize  | `08_rubric_optimize.md`  | `_fb_block(query=…)`                     | failing-checkpoint reasons            | **relevance**        |
| Variant generate | `11_variant_generate.md` | `_fb_block()`                           | — (none)                              | **frequency**        |
| Variant optimize | `12_variant_optimize.md` | `_fb_block(query=…)`                     | failing-checkpoint reasons            | **relevance**        |
| Improve rewrite  | `14_improve_question.md` | `_fb_block(query=…)`                     | reviewer note + question snippet      | **relevance**        |

**The rule:** steps that *author from scratch* or *judge everything* (generate, critic, variant
generate) pass **no query** → inject the most-reinforced rules (frequency). Steps that *fix a specific
failure* (refine, optimize, variant optimize, improve) pass **the problem itself as the query** → the
most *relevant* rule surfaces, even if it's rare.

> **What "basis" means in code.** `relevant_feedback_rules(store, query, k, category)` has one branch:
> if the **query is blank OR `feedback_retrieval_mode == "frequency"`**, it delegates to
> `top_feedback_rules()` (list all rows, sort by `hit_count`, take k — no embeddings). Otherwise it
> **vector-searches** the `("feedback",)` namespace by the query and re-ranks with `_hybrid_rank`
> (similarity + log-`hit_count`) then `_dedup_results`. So the `query=` argument the fix-steps pass
> **only changes behaviour in `semantic`/`hybrid` mode** — see §4 and §Scalability.

> **Default mode is `frequency`** (`settings.py`), so out of the box *every* step above is ranked by
> `hit_count` and the `query=` is ignored. The code already passes the right query everywhere;
> turning on relevance is just `memory_admin backfill` + `FEEDBACK_RETRIEVAL_MODE=hybrid` in `.env`.

> **Only the `rule` strings are injected** — never `hit_count`, `category`, `checkpoint_ref`,
> `aliases`, or any question/session text. The metadata is used only for ranking, dedup, and
> promotion. The category filter (`category=`) is used on the **WRITE side**
> (`rubric.py` `_handle_rejection`, `improve.py`) to give the distiller relevant existing rules as
> context; the READ-into-prompt side uses all top/relevant rules (no category filter).

### 5b. A worked example — one rule, two injections

**Stored once (WRITE).** A reviewer rejects a question at Gate 2: *"Both option 2 and option 4 are
correct — there's no single answer."* `_handle_rejection` (`rubric.py`) tags it category
**Correct Answer Validity**, checkpoint **3.1**, distills it (prompt 10), and `put_feedback_rule`
writes this row into `("feedback",)`:

```json
{
  "rule": "Ensure each MCQ has exactly one unambiguously correct option; no two options may both be defensible.",
  "hit_count": 1,
  "source": "rubric_gate",
  "category": "Correct Answer Validity",
  "checkpoint_ref": "3.1",
  "aliases": []
}
```

**Injected at `generate (03)` by FREQUENCY.** Next run, `process_set` calls `rules_block()` with **no
query** → `top_feedback_rules` → top-8 by `hit_count`. If this rule is among them, prompt 03 receives,
in its `# LESSONS FROM PAST REVIEWS` slot:

```
- Ensure each MCQ has exactly one unambiguously correct option; no two options may both be defensible.
- <7 other most-reinforced rules…>
```
(No problem exists yet, so the basis is popularity — general guidance.)

**Injected at `optimize (08)` by RELEVANCE.** Later, a *new* question fails checkpoint 3.1.
`_run_optimize` builds `query = "Correct Answer Is Definitively Correct: both option 2 and 4 are
valid"` and calls `_fb_block(query=…)`. In `hybrid` mode the query is embedded and vector-searched;
even though the wording differs, the embedding is close, so **this exact rule is retrieved and pasted
into prompt 08** to steer the rewrite — the payoff frequency can't give: a rare-but-perfect rule
surfaces because the *problem* was the query.

---

## 6. What happens during one quiz run

Here is one run from start to finish, showing when lessons are read and written:

```
You click "Generate"
        │
        ▼
[GENERATE node]  nodes.py:233
   → app_store() gives a live pooled Postgres connection
   → SQL SELECT on `store` WHERE prefix='feedback'   ← DB HIT #1 (read rules)
   → top 8 rules become bullet text, pasted into the generate prompt
   → LLM writes MCQs WITH those rules in front of it
        │
        ▼
[CONCEPT-CHECK node]  → LLM checks each MCQ; failures collected
        │
        ▼
[HUMAN GATE]  → you accept / improve / drop  (run pauses here)
        │
        ▼
[COLLECT node]  nodes.py:418-420
   → distill failure + your reasons into generic rules
   → SQL INSERT/UPDATE on `store` (prefix='feedback') ← DB HIT (write rules)
        │
        ▼
[RUBRIC CRITIC node]  rubric.py:261-264
   → load_rubric(): SQL SELECT prefix='rubric_checkpoints' (the 35 checkpoints: 30 base + 5 code-scoped)  ← DB HIT
   → _fb_block(): SQL SELECT prefix='feedback' (rules again)                     ← DB HIT
   → both pasted into the critic prompt; LLM flags failures → Python bands each green/red
        │
        ▼
[RUBRIC GATE]  → you accept/reject; rejections → new rules; recurring → checkpoint promoted
```

So yes — **every run reads feedback + rubric from the DB before each LLM call,
and writes new feedback after each human review.** The `store` table is read and
written many times per run. (Reads are cheap: tiny rows, no embeddings, one
pooled connection reused across the whole process — `memory.py:app_store`.)

Key takeaway: **the rubric checkpoints AND the feedback rules are both just rows
in the `store` table that get loaded fresh and pasted into the prompt each time.**
"Evaluating the rubric" = LLM reading those rows inside the critic prompt.

---

## 7. Full memory flow chart (every namespace, when it's hit)

```
                          ┌──────────────────────────────────────────────┐
                          │            store table (Neon Postgres)        │
                          │     one row = prefix + key + value(JSON)       │
                          └──────────────────────────────────────────────┘
                                              ▲   ▲   ▲   ▲
            INGESTION (one-time per session)  │   │   │   │
   reading material ──► put_chunk()  ─────────┘   │   │   │   prefix=content.*  (EMBEDDED, vector-searchable)
                        put_source() ─────────────┘   │   │   prefix=source.*
                        put_outcomes() ───────────────┘   │   prefix=outcomes.*
            FIRST BOOT
   seed_rubric_if_empty() ────────────────────────────────┘   prefix=rubric_checkpoints / rubric_config

            ════════════════ PER RUN (the live loop) ════════════════

   READ  (start of phases)                     WRITE (after human review)
   ───────────────────────                     ──────────────────────────
   generate   ─ rules_block() ─┐                concept-check fails ─┐
   refine     ─ rules_block() ─┤  prefix=        human drop/improve ─┼─ distill_and_persist()
   critic     ─ _fb_block()  ──┼─ feedback  ◄───  rubric reject ──────┼─ put_feedback_rule()
   variants   ─ _fb_block()  ──┤  (rank by       improve box ─────────┘   (dedupe by hash,
   improve    ─ _fb_block()  ──┘  hit_count)                              hit_count++)
                                                          │
   critic also loads:                                     ▼  hit_count >= 3 (rubric_gate rules)
   load_rubric() ─ prefix=rubric_checkpoints      promote_checkpoint_from_feedback()
                                                  └► appends " Also: ..." to a checkpoint's met_when
                                                     (prefix=rubric_checkpoints)  ← rubric self-evolves
```

Legend: **READ** paths paste rows into a prompt *before* an LLM call. **WRITE**
paths happen *after* a human reviews, turning this run's failures into rules the
*next* run will read. That cross-run handoff is the whole "self-evolving" idea.

---

## 8. See it for yourself — database queries (paste into Neon's SQL Editor)

### A. Orient yourself — how many rows of each kind?
```sql
SELECT split_part(prefix, '.', 1) AS namespace, count(*) AS rows
FROM store
GROUP BY 1
ORDER BY 2 DESC;
```

### B. THE feedback rules, readable (most important query)
```sql
SELECT
  value->>'rule'             AS rule,
  (value->>'hit_count')::int AS hits,
  value->>'source'           AS source,
  value->>'category'         AS category,
  value->>'checkpoint_ref'   AS checkpoint_ref,
  updated_at
FROM store
WHERE prefix = 'feedback'
ORDER BY hits DESC, updated_at DESC;
```
> UI alternative: Tables → Data → Filters → `prefix` `equals` `feedback`.

### C. The top-8 rules the LLM is *actually* injected with (what `top_feedback_rules` returns)
```sql
SELECT value->>'rule' AS rule, (value->>'hit_count')::int AS hits
FROM store
WHERE prefix = 'feedback'
ORDER BY hits DESC
LIMIT 8;
```

### D. Only rules that came from rubric-gate rejections (category-tagged)
```sql
SELECT value->>'rule', value->>'category', value->>'checkpoint_ref', value->>'hit_count'
FROM store
WHERE prefix = 'feedback' AND value->>'source' = 'rubric_gate'
ORDER BY (value->>'hit_count')::int DESC;
```

### E. Rules grouped by where they came from
```sql
SELECT value->>'source' AS source, count(*), sum((value->>'hit_count')::int) AS total_hits
FROM store
WHERE prefix = 'feedback'
GROUP BY 1 ORDER BY 2 DESC;
```

### F. Rules close to promotion (recurring lessons)
```sql
SELECT value->>'rule', (value->>'hit_count')::int AS hits, value->>'checkpoint_ref'
FROM store
WHERE prefix = 'feedback' AND (value->>'hit_count')::int >= 2
ORDER BY hits DESC;
```

### G. PROOF the rubric self-evolved — checkpoints refined by feedback
```sql
SELECT key AS checkpoint_id, value->>'met_when' AS met_when
FROM store
WHERE prefix = 'rubric_checkpoints' AND value->>'met_when' ILIKE '%Also:%';
```

### H. See the 30 rubric checkpoints (what the critic grades against)
```sql
SELECT key AS id, value->>'name' AS name, value->>'category' AS category,
       value->>'scope' AS scope, value->>'met_when' AS met_when
FROM store
WHERE prefix = 'rubric_checkpoints'
ORDER BY key;
```

### I. How big is one session's content vs one feedback row? (why content dominates)
```sql
SELECT prefix, count(*) AS rows, round(avg(length(value::text))) AS avg_value_bytes
FROM store
WHERE prefix LIKE 'content.%' OR prefix = 'feedback'
GROUP BY prefix
ORDER BY rows DESC
LIMIT 20;
```

### J. Newest feedback written (did my last run learn anything?)
```sql
SELECT value->>'rule' AS rule, value->>'source' AS source, updated_at
FROM store
WHERE prefix = 'feedback'
ORDER BY updated_at DESC
LIMIT 10;
```

---

## 9. Verify from the terminal (no SQL needed)

```bash
# Dump every feedback rule with hit_count/source/category, ranked
.venv/bin/python -c "
from backend.memory import app_store, _only
ns=('feedback',)
items=_only(app_store().search(ns, limit=1000), ns)
for it in sorted(items, key=lambda i:i.value.get('hit_count',1), reverse=True):
    v=it.value
    print(v.get('hit_count'), '|', v.get('source'), '|', v.get('category') or '-', '|', v.get('rule'))
print('TOTAL:', len(items))
"

# See exactly what the LLM receives (the injected bullet block)
.venv/bin/python -c "from backend.agent.feedback import rules_block; print(rules_block())"
```

---

## 10. Summary

- Everything the system remembers lives in one table, sorted into kinds by a label column.
- The lessons learned from reviewers are one kind; each row is one general lesson, and a lesson seen
  again just gets a tally mark rather than a duplicate.
- Before writing a quiz, the system reads the most useful lessons and keeps them in mind; after a
  human reviews, it writes any new lessons down.
- A lesson that keeps recurring is promoted into the official quality checklist — so the standards the
  system applies tomorrow are shaped by the corrections it saw today.

---

## Scalability — semantic retrieval + evolve-in-place (non-destructive)

In `semantic`/`hybrid` mode the feedback memory scales as the rule pool grows, on two axes —
**relevance** (the right rule surfaces even when rare) and **no duplicate bloat** (paraphrases of one
lesson merge instead of piling up). **Nothing is ever deleted** — rules evolve.

### What it solves
1. **Top-k by `hit_count` alone can miss important rules.** The globally-most-frequent rules
   aren't necessarily relevant to the problem at hand; a rare-but-perfect rule would stay buried.
2. **Paraphrase-duplicates would pile up.** The distiller rewords the same lesson each run, so
   semantically-identical rules get different `sha256` keys — without semantic dedup they'd become
   separate `hit_count=1` rows.

### The mechanism
`feedback_retrieval_mode` (`"frequency"` | `"semantic"` | `"hybrid"`) defaults to `"frequency"`.
`semantic`/`hybrid` require the rules to be embedded first (`memory_admin backfill`), then set in
`.env`.

- **Write (evolve-in-place).** `put_feedback_rule` embeds new rules (`index=["rule"]`). Before
  inserting, it checks for a semantically-identical rule (cosine ≥ `feedback_dedup_similarity`,
  default **0.85**, same category). If found → **bump that rule's `hit_count` and append the new
  wording to its `aliases`** (the lesson strengthens; no new row). Else insert.
- **Read (relevance).** `relevant_feedback_rules(store, query, k, category)` searches by a
  **description of the problem at hand** — NOT the session topic. The rules are topic-free but
  *dimension*-specific ("answer validity", "distractor quality"), so the query is the failure
  reason / reviewer note / rubric category, which lives in the same vocabulary. Embeddings match
  by meaning, so *"two options are both correct"* retrieves *"each MCQ must have exactly one
  correct answer"* (different words, same concept). Re-ranked by a hybrid of
  similarity + log-`hit_count` (`_hybrid_rank`), then a lexical safety-net dedup (`_dedup_results`).
  Generation (pre-failure) stays on frequency; refine/optimize/improve use the failure as query.
- **Fold (existing duplicates, non-destructive).** `memory_admin fold` clusters existing
  paraphrases per category, sums their `hit_count` onto a canonical, records the others as
  `aliases`, and marks them `superseded_by` (kept in the DB, skipped at read). Reversible.
- **Fallback.** Any embedding error → silently falls back to `top_feedback_rules` (frequency).

### Where it matches (the query is the *problem*, not the topic)
| Phase | Query passed | Strength |
|---|---|---|
| generate (03) | — (frequency / category) | n/a — no problem exists yet |
| refine (05) | concept-check failure reasons | strong |
| critic (07) | — (frequency; all dimensions at once) | n/a |
| optimize (08) | failing-checkpoint reasons | strong |
| variant optimize (12) | failing-checkpoint reasons | strong |
| improve (14) | reviewer's note + question snippet | strong |

### Maintenance commands
```bash
python -m backend.agent.memory_admin backfill [--dry-run]   # embed existing rules (one-time)
python -m backend.agent.memory_admin fold [--category X] [--dry-run]   # merge dup rows (no delete)
```

### UI transparency
`/learned` ("What it learned") lists every active rule with its `hit_count` badge, source/checkpoint
chips, and the folded `aliases` (`GET /api/feedback-rules`). The Rubric view tags any checkpoint
sharpened by promotion (`" Also:"` in `met_when`) with "learned from reviews".

### Cost
Embeddings add ≈ $0.00005/run (one small query embedding per relevant read site; rules embedded
once on write). Negligible vs. the generation/critic LLM spend. Never embed `reading_material`.
