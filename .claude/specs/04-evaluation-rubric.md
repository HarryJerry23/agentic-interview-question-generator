# 04 — Evaluation Rubric (the 35 checkpoints, as-built)

> How a generated question is scored and the pass rule. There is **one rubric**, **no gold/example dataset**, **no file at eval time** — the rubric *is* the criteria and it **lives in memory** (seeded from code, grown by feedback). Scoring is deliberately simple: the LLM critic returns **which checkpoints failed**; Python totals **1 point per met checkpoint, by category**, and computes the band.

## 1. What we score — 35 checkpoints in 6 categories

Defined once in `backend/domain/rubric_seed.py` and **seeded into memory** (`("rubric_checkpoints",)`) on first boot. **30 are per-question (25 base + 5 code-scoped), 5 are per-set.** Each checkpoint may carry an `applies_to_types` (Feature 7): the 5 code checkpoints apply **only to code question types**, so a text question is still scored on the original 25 per-question + 5 per-set and is unaffected.

### Per-question — base (25 checkpoints, 4 categories; apply to every question)
| Category | Checkpoints | Max | Min to pass |
|---|---|---|---|
| **Question Text Quality** | 1.1, 1.2, 1.3, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10 | 9 | 7 |
| **Options Quality** | 2.1–2.8 | 8 | 6 |
| **Correct Answer Validity** | 3.1–3.3 | 3 | **3** (must be perfect) |
| **Pedagogy and Learning Value** | 5.1–5.5 | 5 | 4 |

### Per-question — code-scoped (5 checkpoints, "Code Question Quality"; Feature 7, code questions only)
Applied only when the question's `QUESTION_TYPE` is a code type (`CODE_ANALYSIS`, `CODE_ANALYSIS_MULTIPLE_CHOICE`, `CODE_ANALYSIS_TEXTUAL`, `FIB_CODING`), via each checkpoint's `applies_to_types`.
| Checkpoint | Applies to | Rule |
|---|---|---|
| **6.1** Code shown & complete | all code types | full CODE snippet present, no `…`, code never in the question text |
| **6.2** Code must not reveal the answer | all code types | no give-away comment or printed result |
| **6.3** Expected OUTPUT is correct | textual + FIB | OUTPUT equals what the code actually produces |
| **6.4** FIB single correct blank | `FIB_CODING` | exactly one `<InlineBlank>` at the tested token, correct fill |
| **6.5** Error/fix tied to the LO | code MC | injected error arises only from violating the outcome; minimal fix |

So an applicable max is **25** (text) · **28** (code-analysis MC: 25 + 6.1/6.2/6.5) · **29** (FIB: 25 + 6.1–6.4).

### Per-set (5 checkpoints, 2 categories) — scored on the finished set/variant set
| Category | Checkpoints | Max | Min to pass |
|---|---|---|---|
| **Question Text Quality** (redundancy) | 1.4 | 1 | 1 |
| **Question Type and Format** | 4.1 (type variety), 4.2 (T/F variants), 4.3 (code shown), 4.4 (match) | 4 | 3 |

Every applicable checkpoint must be met to pass (no per-category minimums). Representative per-question checkpoints: **1.1** clarity, **2.1** uniform option length (~50–70 chars), **2.5** plausible distractors, **3.1** answer definitively correct, **5.1** appropriate Bloom level, **5.3** no answer-by-elimination.

## 2. Scoring & pass rule — by category, in Python

The LLM critic (temp 0, prompt 07) returns **only the checkpoints each question FAILS** (anything unlisted is treated as met). `backend/domain/scoring.py::score_question` then tallies points by category and applies the pass rule — **the model never does the arithmetic**.

```python
# backend/domain/scoring.py — the whole rule: strict, all-or-nothing
def score_question(met: dict[str,bool], scope="per_question", question_type=None) -> dict:
    cmax = category_max(scope, question_type)                    # applicable checkpoints for this type
    points = {cat: sum(met.get(c.id, False) for c in CHECKPOINTS
                       if c.scope==scope and c.category==cat
                       and checkpoint_applies(c, question_type)) for cat in cmax}
    passed = all(points[cat] == cmax[cat] for cat in cmax)       # EVERY applicable checkpoint met
    band = "green" if passed else "red"
    return {"category_points": points, "category_max": cmax, "category_min": dict(cmax),
            "points": sum(points.values()), "passed": passed, "band": band}
```

**Pass rule:** a question (or the set) **passes only when every applicable checkpoint is met** — no minimums, no weighting, no normalized fraction, no "critical" flag. The per-category breakdown is kept only to show *what* failed; a single unmet checkpoint fails the whole question.

## 3. The band — a binary gate

| Band | When | Meaning |
|---|---|---|
| 🟢 **green** | every applicable checkpoint met | **pass** — ship it |
| 🔴 **red** | any checkpoint unmet (incl. answer-key, or critic couldn't evaluate) | **fail** — triggers the optimize loop; if still red after the cap → the human gate |

There is **no amber** — the rubric is an unambiguous pass/fail gate. The UI badge (`ScoringCard`/`RubricCard`) shows the category breakdown + the reason for each failed checkpoint, e.g. `Question Text 8/9 · Options 8/8 · Answer 3/3 · Pedagogy 5/5 — "1.3 not met: the stem is framed as an analogy."` (here 8/9 alone → red).

## 4. The rubric lives in memory (not a file)

```
backend/domain/rubric_seed.py (35 Checkpoints + CATEGORY_MIN, code)
        │  seed_rubric_if_empty() on first boot · ensure_rubric_checkpoints() backfills new ids
        ▼
PostgresStore: ("rubric_checkpoints",) + ("rubric_config",)   ← source of truth at eval time
        │  load_rubric()                         │ promotion (feedback)
        ▼                                        ▼
  rubric_score / variants_score            sharpened over time, still in memory
```
- **Seed:** `memory.seed_rubric_if_empty()` inserts the checkpoints + the config once; `memory.ensure_rubric_checkpoints()` (run at warm-up / CLI) idempotently backfills any new checkpoint ids (e.g. the Feature 7 `6.x`) into an already-seeded store without overwriting promoted ones.
- **Read:** `memory.load_rubric()` returns the checkpoints + per-category mins. Served by `GET /api/rubric` (`07`).
- **Validation:** the pydantic `Checkpoint` model in `rubric_seed.py` — there is **no `eval_schema.json`** and no xlsx.

## 5. How the critic uses it (prompt 07, failures-only, batched)

`rubric_score`/`variants_score` build the prompt from the **applicable checkpoints for the scope** + the source + the top feedback rules, and run it on **batches of `critic_batch_size` (8)** questions in parallel (`pmap`):
```
You are a strict MCQ quality critic. Given the source, the rubric checkpoints, and a batch of
questions, return ONLY the checkpoints each question FAILS (with a one-line reason). Anything
unlisted is treated as met.
CHECKPOINTS (id · category · criterion · met_when · examples): {{checkpoints_for_scope}}
FEEDBACK RULES (learned, by category): {{feedback_rules}}
SOURCE (ground truth): {{set_content}}
QUESTIONS: {{questions}}
```
Output schema: `_CriticBatch { scores: [{qid, problems: [{checkpoint, reason}]}] }`. `score_question` turns the problems into points · band · pass.

## 6. Concept coverage (separate from quality)
Before the rubric, `concept_check` (prompt 04, `05`) verifies each generated question covers its **planned outcome**; a miss routes to `refine` (prompt 05), not a per-question rubric fail. Coverage ≠ quality — quality is entirely the rubric checkpoints (redundancy 1.4 and variety 4.1 are set-level).

## 7. The feedback ↔ rubric loop (by category)
1. **Reject → category feedback.** A human rejection (reasons + free text, **mandatory at every gate**) is distilled into one short rule, **tagged with the failed checkpoint's category** (prompt 06 at Gate 1; prompt 10 at Gates 2/3), stored in `("feedback",)` (deduped, `hit_count` bumped), and injected top-rules into the critic + generator next run.
2. **Recurring → checkpoint promotion.** When a rule's `hit_count ≥ rubric_promote_threshold`, `promote_checkpoint_from_feedback(...)` sharpens that checkpoint's `met_when` **in the same category**, in memory. Never crosses categories. (`03 §3`, `06 §7`.)

## Definition of Done
- [ ] The 35 checkpoints (30 base + 5 code-scoped) live in memory (`("rubric_checkpoints",)`), seeded from `rubric_seed.py`; **no xlsx, no `eval_schema.json`**.
- [ ] The LLM returns **failures only**; `score_question` (Python) computes category points + pass + 🟢/🔴 (red = any checkpoint unmet).
- [ ] Pass = **every applicable checkpoint met** (strict, no minimums, no amber); no 1–5 scale / normalized / critical.
- [ ] `per_question` checkpoints (25 base, +5 code-scoped for code questions) gate the rubric/variant loops; `per_set` checkpoints (5) score the finished set.
- [ ] `GET /api/rubric` serves the rubric from memory; feedback is stored by category and promotes a checkpoint within that category (§7).
- [ ] **No gold dataset / few-shot / offline harness anywhere.**
