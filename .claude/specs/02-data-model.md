# 02 — Data Model & Memory Layout (as-built)

> The Pydantic models, the `QuizState` channels + reducers, **the memory layer (LangGraph `PostgresStore`, not raw SQL tables)**, the operational tables, and the portal MD/JSON formats. Names here are canonical. Worked examples + which state feeds which prompt are in `06`. The rubric **lives in memory** (`PostgresStore` namespaces `("rubric_checkpoints",)` + `("rubric_config",)`, §5), seeded from `backend/domain/rubric_seed.py` (`04`).

## 1. Run status

```python
status: "running" | "awaiting_human" | "paused" | "done" | "error" | "stalled" | "dismissed"
```
`paused` is a **reviewer-initiated stop** (Feature 10): the run cooperatively halts at the next checkpoint boundary, is **resumable** from there (`/recover` re-drives from the last committed checkpoint), and — like `stalled` — holds no live thread and costs nothing. A reviewer `cancel` instead lands the run in `dismissed`.

A `workflow` discriminator string (not an enum) is on `QuizState` and the run request: `classroom_quiz` | `mcq_practice` (Feature 8) | `module_quiz` (Feature 9). It selects the graph branch + the output dir (`classroom_quiz/set_NN/`, `mcq_practice/`, or `module_quiz/`). For `module_quiz`, `QuizState` also carries `sessions: List[str]` (the merged session ids) and `module_name: str` (the reviewer-typed name; `session` holds its slug as the run/export identity).

Portal/option vocab used by generation + export:
```python
QUESTION_TYPE ∈ {"MULTIPLE_CHOICE", "MORE_THAN_ONE_MULTIPLE_CHOICE",
                 "CODE_ANALYSIS_MULTIPLE_CHOICE", "CODE_ANALYSIS_TEXTUAL", "FIB_CODING"}  # last 3: Feature 7
BLOOM_LEVEL   ∈ {"REMEMBER","UNDERSTAND","APPLY","ANALYZE","EVALUATE","CREATE"}
VARIANT_TYPE  ∈ {"", "v2","tf_true","tf_false","sb_two","fill","multi","all","none","match",   # text ("" = base)
                 "co","cotf","cerr","cfix","cfun","clogic","ctxt","cfib"}                       # code (Feature 7)
```

## 2. State (`backend/domain/state.py`) — `QuizState`

A `TypedDict`. Channels written by the two parallel `process_set` branches use **reducer annotations**; everything else is last-writer-wins.

| Group | Fields | Reducer | Purpose |
|---|---|---|---|
| **Inputs** | `run_id, course, session, session_title, content_ref, sections, course_outcomes` | — | run identity + the loaded session |
| **Generation** | `set_plan` | `merge_dict` | per-set planned outcomes |
| | `questions` | `merge_questions_by_qid` | generated MCQs (both sets, upsert by qid) |
| | `outcome_checks` | `merge_dict` | concept-check verdicts |
| | `iteration` | `merge_iteration` | scoped refine round per set (max-merge) |
| | `human_decisions, feedback_written, accepted, dropped, needs_attention` | — | Gate 1 results + learning |
| **Rubric** | `rubric_questions, critic_scores, briefings, rubric_iteration, flagged_for_human, rubric_decisions, rubric_approved, rubric_rejected, rubric_summary, promoted_checkpoints` | mix | Gate 2 phase |
| **Variants** | `variants` (`merge_questions_by_qid`), `variant_scores, set_variant_scores, variant_briefings, variant_iteration, variant_decisions, variants_approved, variants_rejected, variant_summary, exported` | mix | Gate 3 phase |
| **Meta** | `status` | — | run status |

Reducers (`state.py`):
```python
merge_dict           = lambda cur, upd: {**cur, **upd}                          # last-writer-wins
merge_questions_by_qid(cur, upd):  d={q.qid:q for q in cur}; d.update({q.qid:q for q in upd}); return list(d.values())  # upsert
merge_iteration(cur, upd):         return {**cur, **{k: max(cur.get(k,0), v) for k,v in upd.items()}}   # scoped max-merge → parallel-safe
```
`merge_questions_by_qid` is an **upsert** — `refine`/`optimize` return the **same qids**, so improved questions replace in place (no duplicate/orphan accumulation). Loop caps (`state.py`): `MAX_REFINE_ROUNDS=3`, `MIN_REFINE_ROUNDS`, `MAX_RUBRIC_ROUNDS=2`, `MAX_VARIANT_ROUNDS=2`.

## 3. Domain models (`backend/domain/models.py`)

```python
class Question(BaseModel):
    qid: str = Field(default_factory=lambda: str(uuid4()))   # internal stable id
    set_label: str = ""                  # "set_a" | "set_b"  (→ set_01 | set_02 on export)
    covers_concept: str = ""             # the planned outcome this Q targets
    topic="" ; sub_topic="" ; concept="" ; question_key="" ; base_question_keys="NA"
    variant_type=""                      # "" for base; "tf_true"|"fill"|"multi"|… for variants
    question_text="" ; content_type="MARKDOWN" ; question_type="MULTIPLE_CHOICE"
    learning_outcome="" ; code="NA" ; code_language="NA"
    options: Dict[str,str] = {}          # OPTION_1..OPTION_n (empty for the option-less code types)
    correct_option=""                    # "OPTION_2" | "OPTION_1, OPTION_3" (multi)
    explanation="" ; bloom_level="UNDERSTAND"
    code_input="" ; expected_output=""   # Feature 7: INPUT/OUTPUT (or INPUT_1/OUTPUT_1) — the answer key for textual/FIB
    eligible_for_rubric: bool = False    # set once it passes concept-check
    needs_attention: bool = False        # still failing after the refine cap
    # helpers (Feature 7): is_code_type, is_optionless, has_code
# Generated/refined questions are emitted as portal `-END-` Markdown blocks and parsed by
# mcq_parser.parse_mcq_blocks; structural_ok() branches by type — options-based types need
# exactly-one-correct (≥1 for multi), 3–5 unique options; option-less code types
# (CODE_ANALYSIS_TEXTUAL, FIB_CODING) instead need CODE + OUTPUT (FIB: one <InlineBlank>). All need a
# non-empty explanation/question and the base↔variant link.

class CriticScore(BaseModel):            # the rubric score — see 04. Binary, by category.
    qid: str
    scope: Literal["per_question","per_set"] = "per_question"
    met: Dict[str,bool] = {}             # {"1.1": True, "2.5": False, …} per APPLICABLE checkpoint
    reasons: Dict[str,str] = {}          # one-line reason per NOT-met checkpoint (only failures returned by the LLM)
    category_points: Dict[str,int] = {}  # computed in Python by score_question
    category_max: Dict[str,int] = {} ; category_min: Dict[str,int] = {}  # category_min == category_max (all required)
    points: int = 0 ; max_points: int = 0
    band: Literal["green","red"] = "red"
    passed: bool = False                 # strict: every applicable checkpoint met

class HumanDecision(BaseModel):    qid: str; action: Literal["accept","edit","drop"]; edited: Optional[Question]=None; reason=""
class RubricDecision(BaseModel):   qid: str; action: Literal["approve","edit","reject"]; edited: Optional[Question]=None; rejection_reasons: List[str]=[]; feedback_text=""
class VariantDecision(BaseModel):  # same shape as RubricDecision (variants gate)
```

A `Checkpoint` model + the 30 seed rows live in `backend/domain/rubric_seed.py` (`04`). There is **no** `WorkflowKind`, `VariantSet`, `MemoryContext`, `AgentParams`, `BloomDistribution`, `FlagEvent`, or `SessionRef` model in the built system — generation is driven directly by the loaded session + injected feedback rules.

## 4. The memory layer — LangGraph `PostgresStore` (not raw SQL)

The pre-build spec proposed hand-rolled SQL tables (`course_content`, `feedback_rules`, …). **As built, memory is LangGraph's `PostgresStore`** wrapped by `backend/memory.py`, organized into namespaces:

| Namespace | Key | Value | Indexed? | Purpose |
|---|---|---|---|---|
| `("content", course, session)` | `content_hash` (sha256) | `{text, chunk_index, heading_path, token_count, session_title, module}` | `["text"]` if embedded, else `False` | session chunks |
| `("source", course, session)` | `"_"` | `{text (full MD), session_title, module}` | `False` | the exact original reading material (assemble loads this — never sampled) |
| `("outcomes", course, session)` | `"_"` | `{session_title, module, outcomes[], confidence}` | `False` | learning outcomes |
| `("rubric_checkpoints",)` | `id` (`"1.1"`…`"6.5"`) | `{id, category, scope, name, criterion, met_when, bad_example, good_example, applies_to_types?}` | `False` | the 35 checkpoints (30 base + 5 code-scoped; `applies_to_types` set on the `6.x`) |
| `("rubric_config",)` | `"{scope}:{category}"` | `{scope, category, min_points}` | `False` | per-(scope,category) required points = full count (strict: all checkpoints must be met) |
| `("feedback",)` | normalized-rule hash | `{rule, hit_count, source, category, checkpoint_ref, aliases[], superseded_by?}` | `["rule"]` when `feedback_retrieval_mode`≠`frequency`, else `False` | learned authoring rules (embedded for semantic retrieval; `aliases` = paraphrases folded in; `superseded_by` set on rows merged by `fold` — kept, skipped at read) |
| `("provenance", run_id)` | zero-padded seq | `{seq, stage, prompt_name, filled, model, started_at, duration_ms, input_tokens, output_tokens, output_summary}` | `False` | every LLM call (cost/latency report) |
| `("run_cost", run_id)` | `"_"` | `{usd, exact}` | `False` | exact OpenRouter spend per run |

Key helpers (`memory.py`): `app_store()` (long-lived pooled singleton; pool has `check=ConnectionPool.check_connection`, `max_idle=120` for Neon resilience), `open_store()` (CLI ctx mgr), `put_chunk` (idempotent), `get_session`, `get_source`, `list_courses`/`list_sessions` (`_retry_once`-wrapped), `seed_rubric_if_empty`, `ensure_rubric_checkpoints` (idempotent backfill of new checkpoint ids, e.g. Feature 7 `6.x`), `load_rubric`, `put_feedback_rule` (exact + semantic dedupe → bump `hit_count` & record paraphrase in `aliases`; non-destructive), `relevant_feedback_rules` (semantic/hybrid retrieval relevant to a problem, with frequency fallback) / `top_feedback_rules` (frequency), `list_feedback_rules` (all active rows w/ metadata → `/api/feedback-rules`), `backfill_feedback_embeddings` + `fold_duplicate_rules` (one-time maintenance, no deletes), `promote_checkpoint_from_feedback`, `put_run_cost`/`get_run_cost`.

> **Char-prefix search gotcha:** `PostgresStore.search` filters by string-prefix; helpers normalize keys/namespaces accordingly (see `feature-03`/memory notes).

## 5. Operational tables (`backend/agent/storage.py::ensure_schema`)

Two operational tables in the agent DB (separate from the memory store):
```sql
CREATE TABLE agent_runs (
  run_id TEXT PRIMARY KEY, course TEXT, session TEXT,
  status TEXT NOT NULL,                       -- running|awaiting_human|paused|done|error|stalled|dismissed
  started_at TIMESTAMPTZ NOT NULL, finished_at TIMESTAMPTZ);

CREATE TABLE agent_step_events (
  id BIGSERIAL PRIMARY KEY, run_id TEXT NOT NULL, node TEXT NOT NULL,
  level TEXT DEFAULT 'info', payload JSONB DEFAULT '{}', ts TIMESTAMPTZ NOT NULL);
CREATE INDEX ON agent_step_events(run_id, id);
```
`reconcile_stalled()` marks orphaned `running` rows `stalled` on startup (a reviewer-`paused` run is already non-`running`, so reconcile leaves it alone — Feature 10). Graph checkpoints are managed by `PostgresSaver.setup()`; the memory store by `PostgresStore.setup()`. **No** `regen_attempts`/`feedback_events`/`course_content`/`run_groups`/`run_sources` tables — those were pre-build proposals.

## 6. Portal MD question format (`-END-` blocks)

Generation + refine + variants emit these blocks; `mcq_parser` parses them; export adds `QUESTION_ID`/`OPTION_x_ID` UUIDs.
```
TOPIC: …
SUB_TOPIC: …
CONCEPT: snake_case_concept
QUESTION_KEY: unique_key            BASE_QUESTION_KEYS: NA | <parent_key>
QUESTION_TEXT: …
CONTENT_TYPE: MARKDOWN              QUESTION_TYPE: MULTIPLE_CHOICE | MORE_THAN_ONE_MULTIPLE_CHOICE
LEARNING_OUTCOME: lowercase_snake   CODE: NA            CODE_LANGUAGE: NA|PYTHON|JS|…
OPTION_1: …   OPTION_2: …   OPTION_3: …   OPTION_4: …
CORRECT_OPTION: OPTION_2            EXPLANATION: …
BLOOM_LEVEL: UNDERSTAND
-END-
```
**Code question types (Feature 7)** carry a real `CODE` + `CODE_LANGUAGE`. The option-less ones drop `OPTION_*`/`CORRECT_OPTION` and instead emit `INPUT`/`OUTPUT` (`CODE_ANALYSIS_TEXTUAL`) or `INPUT_1`/`OUTPUT_1` with one `<InlineBlank>answer</InlineBlank>` in the `CODE` (`FIB_CODING`):
```
QUESTION_TYPE: CODE_ANALYSIS_TEXTUAL        QUESTION_TYPE: FIB_CODING
CODE: <snippet, not in backticks>           CODE: …<InlineBlank>ans</InlineBlank>…
CODE_LANGUAGE: PYTHON                        CODE_LANGUAGE: PYTHON
INPUT:                                       INPUT_1:
OUTPUT: <exact output>                       OUTPUT_1: <output after filling the blank>
```
Variants set `BASE_QUESTION_KEYS=<base key>` and `QUESTION_KEY=<base>_<suffix>` (suffix = variant type). Matches the portal `generative_ai_mcq_sets/**` shape.

## 7. Portal JSON format + export layout

`build_set_files` (`backend/agent/export.py`) emits, per set, an `.md` (the `-END-` blocks) and **two** JSON arrays split by content type — sharing the same per-question/option UUIDs — because the portal loads each upload as two members:

- **`Default_new/{base}.json`** — the standard types (`MULTIPLE_CHOICE`, `MORE_THAN_ONE_MULTIPLE_CHOICE`):
```json
{ "question_id": "<uuid>", "question_key": "…", "skills":[], "toughness":"EASY", "question_type": "MULTIPLE_CHOICE",
  "question": {"content":"…","content_type":"MARKDOWN","tag_names":["<BLOOM>","<sub_topic>","<topic>","<outcome>","<key>"],"multimedia":[]},
  "options": [{"content":"…","content_type":"MARKDOWN","is_correct":true,"multimedia":[]}, …],
  "explanation_for_answer": {"content":"…","content_type":"MARKDOWN"} }
```
- **`Code Analysis MCQs/{base}.json`** — the code-analysis types (`CODE_ANALYSIS_MULTIPLE_CHOICE`, `CODE_ANALYSIS_TEXTUAL`, `FIB_CODING`), in the portal's **code schema** (`question_text` flat; `code_metadata:[{is_editable,language,code_data,default_code}]`; `input_output:[…]`). For **MC** the id is nested in `input_output[0]` with `wrong_answers[]` + `output[]` (the correct option text(s)); for **TEXTUAL/FIB** there is a top-level `question_id` + `reference:""` and `input_output[0].output:[<expected output>]` (no `wrong_answers`). Split is by `Question.is_code_type`.

On-disk layout (`generated_quizzes_dir`) mirrors the two zip members; a member is written only when non-empty:
```
generated_quizzes/{course}/{session}/classroom_quiz/
  set_01/  reading_material.md · classroom_quiz.md (-END-) · Default_new/{base}.json · [Code Analysis MCQs/{base}.json]
  set_02/  …
  {session}_set_01_classroom_quiz.zip   → members Default_new/{base}.json  +  Code Analysis MCQs/{base}.json
  {session}_set_02_classroom_quiz.zip
```
The zip filename (`{base}.zip`) is unchanged; only its contents are split. `mcq_practice` and `module_quiz` exports use the same two-member split under their own dirs. A re-run **replaces** (not appends) the set folders. (`05` finalize/export; `07` API.)

## Definition of Done
- [ ] `Question`, `CriticScore`, `HumanDecision`, `RubricDecision`, `VariantDecision`, `Checkpoint` are implemented; `QuizState` validates + round-trips.
- [ ] Reducers are commutative; the two `process_set` branches merge with no loss (`merge_questions_by_qid` upserts by qid; `merge_iteration` max-merges).
- [ ] Memory is the LangGraph `PostgresStore` with the §4 namespaces; the rubric self-seeds; pools survive Neon idle drops. No raw `course_content`/`feedback_rules` SQL tables; **no** gold/eval table, xlsx, or `eval_schema.json`.
- [ ] `agent_runs` + `agent_step_events` exist; `reconcile_stalled()` runs on boot.
- [ ] MD↔JSON round-trips to the portal format (UUID ids, `is_correct`, `explanation_for_answer`); the set folders + zips match the existing MCQ-set shape.
