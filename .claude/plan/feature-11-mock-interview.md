# Feature 11 — Mock Interview (harvest REAL, evidenced interview questions)

> Step-by-step build plan. A 4th product type alongside Classroom Quiz, MCQ Practice, Module Quiz.
> Contract: `.claude/specs/10-mock-interview.md`. This file says **exactly what to implement**, in order.

## Context

Build a **harvest-and-verify** workflow `mock_interview`. The user selects several sessions of a topic;
the system extracts their key outcomes, **harvests real interview questions** asked at real companies
from legitimate web sources, **verifies the evidence** (every question needs >1 independent source + a
named company + resolving links — no padding), and writes a **Markdown table** of question · outcome ·
companies (linked) · # companies · source links. The LLM **never writes a question or invents a
company**. Evaluation criteria live in a **self-evolving `SKILL.md`**, not a DB rubric. One **exception-
only** human gate. On-demand (no scheduler). Reuse the engine; keep it a separate workflow.

## Delivery — 3 parts (each part ends in a RUNNABLE app)

Built as **3 vertical slices** (each runs end-to-end), not horizontal layers. The detailed step specs
follow this overview, tagged `[P1]/[P2]/[P3]`.

### PART 1 — Walking skeleton: end-to-end with the GitHub source only
*Goal: prove the whole pipeline produces a real Markdown table from the UI, using the easiest source.*
- **Includes:** Step 1 (wiring+state, full) · Step 2 *(only the GitHub bits: `httpx`/`PyGithub` dep,
  `interview_github_repos` default, github enable flag)* · Step 3 *(only `sources/base.py` +
  `sources/github_repo.py`)* · Step 5 *(`extract_outcomes`, `harvest` GitHub-only, a **simple**
  `evidence_gate`, `export_md`; **no** ≤3-round loop, **no** cross-source corroboration, **no** human
  gate → auto-publish all)* · Step 6 *(bank put/get, exact-text dedup OK for now)* · Step 7 (export
  layout, full) · Step 8 *(prompts 20 + 21; fold a minimal check into `evidence_gate`)* · Step 9
  *(`api.startMockInterview`, the 4th button + multi-session picker, render the md table; **no**
  `InterviewTable` gate yet)*.
- **Relaxed evidence bar:** single source OK (only one connector exists). Strictness arrives in Part 2.
- **✅ Definition of Done:** in the UI, pick a course → sessions → **Mock Interview** → run → get a real
  `mock_interview.md` table sourced from the GitHub repos. Existing workflows unaffected.

### PART 2 — Real sourcing + the evidence engine
*Goal: production-quality, multi-company, deduped, strictly-evidenced questions from all 60 sources.*
- **Includes:** Step 2 *(remainder: `TAVILY_API_KEY`, `crawl4ai`/`trafilatura` deps, all connector flags,
  activate `interview_source_allowlist`)* · Step 3 *(remainder: `tavily_search.py`, `geeksforgeeks.py`,
  `reddit.py`, `ambitionbox.py`-if-allowed; registry returns all enabled)* · Step 5 *(upgrade `verify`:
  the **≤3-round verify⟲research loop**, **cross-source corroboration → distinct company count + links**,
  the **strict >1-independent-source bar**)* · Step 6 *(embedding dedup-on-write, merge companies/sources,
  accumulate across runs)* · Step 8 *(prompt 22, full grounded verification)*.
- **✅ Definition of Done:** a run harvests across all 60 sources, verifies strictly (drops fabricated/
  single-source), dedupes, and emits multi-company evidenced rows; re-running a topic **merges + grows
  `company_count`**. Still auto-publishes (human gate is Part 3), but evidence is now real.
- **BUILT — notes / deviations:**
  - **One Tavily connector covers the whole allowlist** (GeeksforGeeks, AmbitionBox, Glassdoor, Levels,
    Blind, **Reddit**, the listicles, …) legitimately via search — *no* separate `geeksforgeeks.py` /
    `ambitionbox.py` / `reddit.py` scrapers in this build (cleaner + avoids ToS-violating scraping of
    anti-bot sites). A dedicated GFG/Reddit API connector remains a future option.
  - **Evidence engine** (`mock_interview.verify`): embed→`_greedy_cluster` cross-source → bounded
    ≤`interview_research_rounds` Tavily research loop on under-bar groups → link-resolve (anti-bot
    401/403/429 still counts as "exists") → grounded check (prompt 22) → publish only with
    **≥`interview_min_sources` (2) distinct live domains + an evidence-supported company**.
  - **Dedup threshold calibrated to 0.84** on text-embedding-3-small (identical 1.0 · paraphrase ~0.85 ·
    distinct ≤0.7). Bank merge verified live: two paraphrasings → one row, 2 companies, 3 sources.
  - **Requires `TAVILY_API_KEY`** for the web sources. Without it only the GitHub connector runs and the
    strict bar holds every single-source question (published 0) — by design, not a regression.

### PART 3 — Human-in-the-loop + self-evolving skill + polish
*Goal: the complete, self-improving, minimal-human-intervention app.*
- **Includes:** Step 4 (full: `SKILL.md` + `interview_skill.py`) · Step 5 *(the publish-vs-queue split +
  `interview_gate` interrupt over **queued rows only**; `export_md` reject → distill → append learned
  rule)* · Step 9 *(remainder: `InterviewTable.jsx` queue review, `useAgentRun` gate handling, History)*.
- **✅ Definition of Done:** the exception-only review queue works; rejecting a row **teaches the
  `SKILL.md`** (learned rules grow → fewer rows queued next run); full regression + `npm run build` pass.
- **BUILT — notes:**
  - **Skill** at `.claude/skills/verifying-interview-evidence/SKILL.md` (hard checks + a `## Learned
    rules` section); `backend/agent/interview_skill.py` = `load_skill_text` / `learned_rules` /
    `append_learned_rule` (git-versioned file writes; verified append/parse/idempotent).
  - **verify split** → PUBLISH (≥`interview_min_sources` live domains + a grounded company → auto) /
    QUEUE (real + on-topic but under-evidenced → human) / DROP (fabricated / not-a-question / no live
    source). Prompt 22 now takes a `{{learned_rules}}` block (the skill's rules steer grounding).
  - **`interview_gate`** node interrupts **only when queued rows exist** (corroborated runs skip it →
    minimal intervention). Decisions keyed by `qid` (reuses the existing resume contract).
  - **`export_md`** applies decisions: untouched/approve/edit → publish to bank; **reject → `_distill_rule`
    (inline LLM) → `append_learned_rule`** (interview learning lives ONLY in SKILL.md, never the MCQ
    feedback namespace). Table rebuilt from the bank.
  - **Frontend:** `InterviewTable.jsx` (queue review: approve / reject-with-reason), `useAgentRun`
    captures gate `"interview"` cards, `Generate.jsx` renders the gate; `npm run build` passes.

---

## Detailed step specs (tagged by Part)

### Step 1 — Workflow wiring + state  `[P1]`
- `backend/api/agent.py`: add `"mock_interview"` to `WORKFLOWS`. In `/run`, accept
  `{course, sessions[], topic_name}` (same shape as `module_quiz`); set `session = slugify(topic_name)`;
  validate non-empty. `/exists`: map `sub = "mock_interview"`.
- `backend/domain/state.py`: add `QuizState` fields — `topic_name: str`, and the harvest/verify slices:
  `outcomes: List[str]`, `candidates: List[dict]`, `verified: List[dict]`, `queued: List[dict]`,
  `interview_iteration: int`. Reuse the existing `sessions: List[str]` / merge reducers.
- `backend/agent/graph.py`: register nodes `extract_outcomes`, `harvest`, `verify`, `interview_gate`,
  `export_md`; extend `_route_after_assemble` with `"mock_interview" → "extract_outcomes"`; add edges
  `extract_outcomes → harvest → verify → interview_gate → export_md → END`. Existing branches untouched.

### Step 2 — Settings + dependencies  `[P1 GitHub bits · P2 the rest]`
- `requirements.txt`: add `tavily-python`, `crawl4ai`, `trafilatura`, `httpx` (and `PyGithub` or use raw
  `httpx` for GitHub).
- `backend/settings.py`: add `tavily_api_key`, `interview_dedup_similarity: float = 0.88`, per-connector
  enable flags (`interview_src_github_enabled`, `_gfg_`, `_ambitionbox_`, `_reddit_`, `_tavily_`),
  optional `reddit_client_id`/`reddit_client_secret`, optional `github_token`, and the two list defaults
  **seeded from spec §F.2**:
  - `interview_source_allowlist: list[str]` = the **VERIFIED** domains of catalog groups A1+A2+A3+B1
    (spec §F.2, entries 1–48): tryexponent.com, datalemur.com, stratascratch.com, prachub.com,
    interviewquery.com, prepfully.com, igotanoffer.com, glassdoor.com, teamblind.com, leetcode.com,
    indeed.com, interviewing.io, hellointerview.com, ambitionbox.com, geeksforgeeks.org, interviewbit.com,
    prepinsta.com, indiabix.com, naukri.com, reddit.com, medium.com, quora.com,
    datascience.stackexchange.com, stats.stackexchange.com, stackoverflow.com, datacamp.com,
    analyticsvidhya.com, kdnuggets.com, towardsai.net, towardsdatascience.com, tredence.com, igmguru.com,
    vinsys.com, novelvista.com, generativeaimasters.in, blockchain-council.org, amquesteducation.com,
    simplilearn.com, edureka.co, intellipaat.com, projectpro.io, turing.com, springboard.com,
    mlstack.cafe, 365datascience.com, builtin.com.
  - `interview_github_repos: list[str]` = catalog group **C** (spec §F.2, entries 49–60):
    `llmgenai/LLMInterviewQuestions`, `amitshekhariitbhu/ai-engineering-interview-questions`,
    `amitshekhariitbhu/machine-learning-interview-questions`, `Devinterview-io/llms-interview-questions`,
    `shafaypro/CrackingMachineLearningInterview`, `khangich/machine-learning-interview`,
    `alirezadir/Machine-Learning-Interviews`, `andrewekhalel/MLQuestions`,
    `kojino/120-Data-Science-Interview-Questions`, `youssefHosni/Data-Science-Interview-Questions-Answers`,
    `rbhatia46/Data-Science-Interview-Resources`, `Sroy20/machine-learning-interview-questions`.
  These 60 were already URL-verified (spec §F.2/F.4); the 12 that failed are excluded. Re-check robots/ToS
  only for the anti-bot ones (marked `(→search)` in §F.2) before enabling a *direct* scraper for them.
- `.env` / `.env.example`: add `TAVILY_API_KEY` (+ optional Reddit/GitHub tokens) and the toggles.

### Step 3 — Source-connector layer (the core)  `[P1 base+github · P2 tavily/gfg/reddit/ambitionbox]`
New package `backend/agent/sources/`. Each connector exposes
`fetch(outcomes: list[str]) -> list[Record]`, `Record = {question_text, company|None, source_url,
raw_snippet, source_type}`. A registry returns the **enabled** connectors (per settings flags).
- `base.py` — `Record` dataclass, `Connector` protocol, `enabled_connectors()` registry, a shared
  `polite_get()` (descriptive UA, rate-limit, robots check, retries) and `extract_text()` (`trafilatura`).
- `github_repo.py` — pull each configured repo's markdown via the GitHub API; parse Q + any company
  mentions; **attribution** source. License-clean, no anti-bot.
- `geeksforgeeks.py` — discover new Interview-Experience URLs via the sitemap/RSS (path is robots-
  allowed); `polite_get()` + `extract_text()`; **attribution**; store question + link only.
- `tavily_search.py` — Tavily search over the full `interview_source_allowlist` (the ≥50-domain catalog,
  spec §F.2 groups A1+A2+A3+B1); returns extracted content; this single connector is what makes the
  catalog "50+" — it reaches every allowlisted attribution + content/corroboration site without a
  bespoke scraper. The breadth layer.
- `ambitionbox.py` — dedicated connector **only if** a build-time `robots.txt`/ToS check passes; else
  leave disabled and rely on Tavily.
- `reddit.py` — optional; official API via credentials; **attribution**.
Each connector must extract **verbatim** (no inferred company names) and attach the exact `source_url`.

### Step 4 — The skill (evaluation, self-evolving)  `[P3]`
- Create `.claude/skills/verifying-interview-evidence/SKILL.md` with the hard checks from spec §E and an
  empty `## Learned rules` section.
- `backend/agent/interview_skill.py` — `load_skill_text()` (read the SKILL.md), `learned_rules()` (parse
  the section), `append_learned_rule(rule: str)` (write a new bullet, git-versioned on disk).

### Step 5 — The 3 agents + gate + export (`backend/agent/mock_interview.py`)  `[P1 basic · P2 verify loop · P3 gate+evolve]`
- `extract_outcomes(state)` — merged body (from `assemble`) → outcomes via new prompt
  `20_interview_outcomes.md` (model on `18_module_plan.md`). Emit `event: outcomes`.
- `harvest(state)` — `pmap` over outcomes × `enabled_connectors()`; for fetched pages, run prompt
  `21_interview_harvest.md` to pull literal `{question, company, url}`; collect `candidates`. Emit
  `event: harvest` with counts per source.
- `verify(state)` — `pmap` over candidates; per candidate run `22_interview_verify.md` (grounded: does
  the live page contain this question + company?), cross-source corroborate, count distinct companies;
  then call `evidence_gate(candidate)` (deterministic) → `published`/`queued`/`dropped`. Re-search weak
  ones up to `MAX_REFINE_ROUNDS = 3`. Dedup vs the bank via embeddings (`interview_dedup_similarity`).
  Write `published` rows to the bank; carry `queued` rows to the gate. Emit `event: verify`.
- `evidence_gate(candidate)` — pure function implementing spec §E hard checks; injects `learned_rules()`
  into the verify prompt context.
- `interview_gate(state)` — `interrupt()` exposing **only** `queued` rows with their evidence; resume
  applies `approve | edit | reject` (reject reason required). Reuse the gate decision plumbing from the
  other gates (`{qid: decision}`).
- `export_md(state)` — write `mock_interview.md` (GFM table, ordered by company_count desc) +
  `mock_interview.json` under the export dir; mark approved rows `published`; for each reject reason call
  `feedback.distill_and_persist` then `interview_skill.append_learned_rule(...)`.

### Step 6 — Memory (`backend/memory.py`)  `[P1 basic put/get · P2 embedding dedup+merge]`
- Add the `("interview_bank", course, topic_slug)` namespace (indexed on `question_text`).
- Helpers: `put_interview_question(...)` (embedding dedup-on-write → merge companies/sources + recompute
  `company_count`, else insert), `get_interview_bank(course, topic)`, `mark_interview_published(...)`.
- Call nothing new from `warm_agent` (no rubric seed for this workflow).

### Step 7 — Export layout (`backend/agent/export.py`)  `[P1]`
- Add a `mock_interview` branch to `_layout` → dir `mock_interview/`, file base `mock_interview`. Write
  a Markdown **table** (not `-END-` blocks) + the json. **No portal zip** for this workflow.

### Step 8 — Prompts (`backend/agent/prompts/`)  `[P1 prompts 20+21 · P2 prompt 22]`
- `20_interview_outcomes.md` — extract key outcomes/skills from the merged sessions.
- `21_interview_harvest.md` — from fetched page text, extract the **literal** question + named company +
  source URL; explicitly forbid inventing/guessing companies.
- `22_interview_verify.md` — grounded verification: confirm the page contains the question + company;
  judge outcome-relevance; include the skill's hard checks + `Learned rules`.

### Step 9 — Frontend  `[P1 button+picker+table render · P3 InterviewTable queue+gate]`
- `frontend/src/lib/api.js` — `startMockInterview(course, sessions, topicName)` (mirror
  `startModuleQuiz`).
- `frontend/src/pages/Generate.jsx` — a 4th **Mock Interview** workflow button; reuse the module-quiz
  multi-session checklist + topic-name input. A mock-interview run renders a **table** (flat), and the
  gate shows only queued rows.
- `frontend/src/components/InterviewTable.jsx` (new) — renders candidate/queued rows as a table with
  per-row approve/edit/reject; reuse `GateBanner`, `RejectBox`, `Markdown` (GFM tables). Submit via
  `api.resumeRun(runId, decisions)`.
- `frontend/src/hooks/useAgentRun.js` — recognize `workflow:"mock_interview"` + gate `"interview"`; new
  `set` key `"interview"`.
- `History.jsx` — no change (workflow-agnostic).

## Verification (end-to-end)

1. Backend imports/compile OK. Each connector returns normalized records for a sample outcome in a REPL
   (`github_repo` via API; `geeksforgeeks` via an allowed sitemap URL; `tavily_search` over the
   allowlist; `reddit`/`ambitionbox` only if enabled).
2. **Anti-hallucination:** feed `verify` a candidate with a 404/fabricated URL and a wrong company → both
   dropped; a single-source candidate → re-search loop runs, then `queued` (never padded into the table).
3. **Happy path (UI):** course → select sessions → **Mock Interview** → run. SSE
   `assemble → extract_outcomes → harvest → verify → (auto-publish | awaiting_human)`. Confirm
   `mock_interview.md` lists only rows with ≥1 named company + ≥2 resolving links, ordered by # companies.
4. **Skill self-evolves + low intervention:** reject a queued row with a reason → a bullet is appended to
   `.claude/skills/verifying-interview-evidence/SKILL.md` `## Learned rules`; a re-run applies it (fewer
   rows queued) and **merges duplicates / grows company_count** instead of duplicating.
5. Regression: classroom / practice / module runs unchanged.
6. `cd frontend && npm run build`.
