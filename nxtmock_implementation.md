# NxTMock (Mock Interview) — Implementation Reference

> **Purpose:** Context document for agents working on Feature 11. Read this before touching any
> `mock_interview*`, `interview_skill*`, or `sources/` file. It describes the complete pipeline,
> each node's contract, the evidence engine, and every design decision that would otherwise need
> re-deriving from source.

---

## 1. Core Principle

> **The LLM never authors a question and never invents a company.**

Its only jobs are:
1. Extract the selected sessions' **key learning outcomes / skills** (what to search for)
2. **Find** real interview questions tied to those outcomes from legitimate web sources
3. **Extract** them verbatim, with evidence
4. **Verify** the evidence is real and attributable to a named company

Every published question must have **> 1 independent legitimate source + at least one named company + resolving links**. Company counts are never padded.

NxTMock is the 4th product workflow alongside `classroom_quiz`, `mcq_practice`, and `module_quiz`. The API field is `workflow="mock_interview"`.

---

## 2. End-to-End Architecture

```
POST /api/agent/run  {workflow: "mock_interview", course, sessions[], topic_name}
  │
  ▼
assemble              reused node — merges selected session bodies into state
  │
  ▼
extract_outcomes      Agent 1 · prompt 20 · names interview-relevant outcomes/skills
  │
  ▼
harvest               Agent 2 · prompt 21 · fans out across GitHub + Tavily connectors
  │
  ▼
verify ⟲ research     Agent 3 · prompt 22 · clusters, corroborates, ≤3 research rounds
  │
  ├─ published → auto, no human
  └─ queued    ─▶ interview_gate   👤 human review (approve / edit / reject)
                       │
                       ▼
                  export_md         writes mock_interview.md + .json
                                    appends distilled reject reasons → SKILL.md
```

**Graph wiring** (`backend/agent/graph.py`):
```python
g.add_node("extract_outcomes", extract_outcomes)
g.add_node("harvest",          harvest)
g.add_node("verify",           verify)
g.add_node("interview_gate",   interview_gate)
g.add_node("export_md",        export_md)

g.add_edge("extract_outcomes", "harvest")
g.add_edge("harvest",          "verify")
g.add_edge("verify",           "interview_gate")
g.add_edge("interview_gate",   "export_md")
g.add_edge("export_md",        END)
```

**Routing fork** (after `assemble`):
```python
if wf == "mock_interview":
    return "extract_outcomes"
```

---

## 3. LangGraph Nodes

All node functions live in `backend/agent/mock_interview.py`.

### Node 1 — `extract_outcomes`

| | |
|---|---|
| **Reads state** | `merged_content`, `sessions`, `topic_name` |
| **Writes state** | `interview_outcomes: List[str]` |
| **Prompt** | `prompts/20_interview_outcomes.md` |
| **Cap** | `_OUTCOMES_CHAR_CAP = 16_000` chars per session |

Calls `_outcomes_for_one()` per selected session using the LLM (prompt 20), then merges results with order-preserving dedupe. Each outcome is a `lowercase_snake_case` phrase (3–5 words, e.g. `rag_evaluation_metrics`). These outcomes become the search targets for the harvest step.

---

### Node 2 — `harvest`

| | |
|---|---|
| **Reads state** | `interview_outcomes` |
| **Writes state** | `interview_candidates: List[Dict]` |
| **Prompt** | `prompts/21_interview_harvest.md` |
| **Caps** | `_HARVEST_BATCH = 50`, `_MAX_FILTER_CANDIDATES = 240` |

1. Calls `enabled_connectors()` → returns active connectors (GitHub + Tavily by default)
2. Each connector's `fetch(outcomes)` returns `List[Record]`
3. All records pooled → deduped on normalized question text
4. LLM filters in `_HARVEST_BATCH`-sized batches via prompt 21: keep only genuine, on-topic interview questions; tag each with matching outcome
5. Returns up to `_MAX_FILTER_CANDIDATES` filtered candidates

---

### Node 3 — `verify`

| | |
|---|---|
| **Reads state** | `interview_candidates`, `interview_outcomes` |
| **Writes state** | `interview_rows` (published), `interview_queued` (under-evidenced), `interview_iteration` |
| **Prompt** | `prompts/22_interview_verify.md` |
| **Caps** | `_RESEARCH_GROUP_CAP = 20`, `_MAX_LIVE_CHECK_URLS = 200`, `interview_research_rounds ≤ 3` |

Full evidence engine — see §5 for detail.

---

### Node 4 — `interview_gate`

| | |
|---|---|
| **Reads state** | `interview_queued` |
| **Writes state** | `interview_decisions: Dict[str, Any]` |
| **Human interrupt** | Yes — ONLY for rows in `interview_queued` |

Exception-only gate. If nothing is queued, passes straight through. When queued rows exist, suspends the run and sends them to the frontend (`InterviewTable.jsx`). Reviewer can **approve / edit / reject** each row. Rejections require a reason; the reason is later distilled into a SKILL.md learned rule.

---

### Node 5 — `export_md`

| | |
|---|---|
| **Reads state** | `interview_rows`, `interview_queued`, `interview_decisions`, `topic_name` |
| **Writes state** | nothing (side effects only) |
| **Cap** | `_MAX_RULES_PER_RUN = 5` learned rules per run |

1. Applies gate decisions: approve/edit → move row to published; reject → `_distill_rule()` → `append_learned_rule()` via `interview_skill.py`
2. Sorts published rows by `company_count` descending
3. Writes `mock_interview.md` (GFM table) + `mock_interview.json`
4. Output path: `generated_quizzes/<course>/<topic_slug>/mock_interview/`

---

## 4. Source Connectors

All connector code lives under `backend/agent/sources/`.

### `base.py` — Shared Infrastructure

**`Record` dataclass** — unit of harvested data:
```python
@dataclass
class Record:
    question_text: str
    source_url:   str
    company:      Optional[str] = None
    raw_snippet:  str = ""
    source_type:  str = ""        # e.g. "github:owner/repo", "tavily:glassdoor.com"
```

**`Connector` protocol** — interface every connector must implement:
```python
class Connector(Protocol):
    name: str
    def fetch(self, outcomes: List[str]) -> List[Record]: ...
```

**`is_safe_public_url(url)`** — SSRF guard called before every network fetch. Checks:
- Scheme is `http` or `https`
- Hostname resolves
- Resolved IP is not in RFC-1918, loopback, link-local, cloud-metadata (169.254.169.254), reserved, or multicast ranges

**`polite_get(url, ...)`** — HTTP GET with:
- Browser-like User-Agent: `nxtwave-mock-interview-bot/1.0 (+https://www.ccbp.in; gen-ai-content@nxtwave.co.in)`
- SSRF guard on every call
- Backoff on 403/429/network errors (2 retries)

**`enabled_connectors()`** — reads settings to return active connectors list.

---

### `github_repo.py` — GitHub Connector

- **`name = "github"`**
- Uses GitHub REST API (`https://api.github.com`) — optional Bearer token lifts rate limit from 60 → 5000 req/hr
- Reads `settings.interview_github_repos` (26 repos, validated `owner/repo` format)
- Per repo: fetches file tree → filters `.md` files → reads up to `_MAX_FILES_PER_REPO = 15`
- Extracts question-like lines (ends in `?` or starts with a question word, 15–320 chars)
- Filters by outcome token overlap (`_outcome_tokens` — words ≥ 4 chars)
- Dedupes on normalized question text
- Returns Records with `company=None`, `source_type="github:owner/repo"`
- Caps at `_MAX_CANDIDATES = 600`
- Skips: `LICENSE`, `CONTRIBUTING`, `CHANGELOG`, `node_modules` files

---

### `tavily_search.py` — Web Search Connector

- **`name = "tavily"`**
- Uses Tavily API — key from `settings.tavily_api_key`
- Searches up to `_MAX_OUTCOMES = 14` outcomes
- Per outcome, runs **two passes**:
  1. **Broad pass**: `"{outcome} interview question asked at company"` across entire `interview_source_allowlist` (67 domains)
  2. **Company-attribution pass**: `"{outcome} interview questions"` restricted to `_ATTRIBUTION_DOMAINS` (13 company-tagged sites: Glassdoor, AmbitionBox, Exponent, Levels, LeetCode, etc.)
- Caps at `_MAX_RECORDS = 800` total records

**Company attribution order** (per result):
1. URL pattern match (`_company_from_url`) — AmbitionBox `/interviews/<co>-`, Glassdoor `/Interview/<co>-`, Levels `/companies/<co>/`, Exponent `/guides/<co>/`
2. Page title text (`_company_from_text`) — e.g. "Amazon Interview Questions" → "Amazon"
3. Page text head (first 200 chars)

**`search_question(question)`** — used by the research loop in `verify`:
1. Broad corroboration: `"{question}" interview asked at company` (whole allowlist)
2. Per-company-site quoted probes on AmbitionBox + Glassdoor for precision

---

## 5. Evidence Engine & Verification

All logic in `mock_interview.verify()` and `mock_interview.evidence_gate()`.

### Step-by-step

1. **Embed** all candidates with `text-embedding-3-small` (dims=1536)
2. **Greedy cluster** by cosine similarity ≥ `interview_dedup_similarity` (default 0.84) — identical/paraphrase questions from different sources collapse into one group
3. **Aggregate** each cluster: union of source URLs, company hints, snippets
4. **Resolve links** — `_link_alive()` HEAD/GET each URL (SSRF-guarded); anti-bot 401/403/429 = alive; 404/410/DNS-dead = dead
5. **Company attribution** — `_url_companies()` parses company from trusted URL patterns; `_company_objs()` pairs names with proof URLs
6. **Ground** via prompt 22 — LLM confirms: is this a genuine question? Which companies does the evidence actually support? (Injected with SKILL.md learned rules)
7. **Research loop** — groups failing the evidence bar get up to `interview_research_rounds` (default 3) re-searches via `search_question()`; new Records merged into the group
8. **`evidence_gate()`** — deterministic Python gate applies hard checks:

| Check | Condition |
|---|---|
| Real | Question text present on a fetched page |
| >1 source | Corroborated by >1 independent domain |
| Named company + live links | ≥1 explicitly named company; all cited links resolve |
| Outcome-relevant | Maps to one of `interview_outcomes` |
| Not duplicate | Below embedding-dedup threshold vs published bank |
| Safe | Genuine interview question; no PII, nothing offensive |

**Verdict:**
- **Publish** — all 6 checks pass → `interview_rows`
- **Queue** — real question but under-evidenced (1 source, or company unproven) → `interview_queued`
- **Drop** — fabricated, off-topic, no live source → discarded

### Company-URL Trust Rule
A company parsed from a company-keyed URL (AmbitionBox `/interviews/<co>-`, Glassdoor `/Interview/<co>-`, Exponent `/guides/<co>/`, Levels `/companies/<co>/`) is treated as **authoritative proof** — the page *is* that company's interview page. A question with one such URL can publish even without a second independent source (relaxes the >1 source check for this case only).

---

## 6. SKILL.md — Self-Evolving Verification Criteria

**Location:** `.claude/skills/verifying-interview-evidence/SKILL.md`

**Read by:** `backend/agent/interview_skill.py`

The SKILL.md file contains the hard checks (§5 above) and a `## Learned rules` section that grows automatically from reviewer rejections. The LLM reads these rules during prompt 22 (`{{learned_rules}}`), so the system gets sharper over time without code changes.

**`interview_skill.py` API:**

| Function | Purpose |
|---|---|
| `skill_path()` | Returns `Path` to SKILL.md |
| `load_skill_text()` | Reads full SKILL.md (returns `""` on error) |
| `learned_rules()` | Parses and returns bullets under `## Learned rules` |
| `append_learned_rule(rule)` | Idempotently appends a new bullet; returns True if written |

**Self-evolution path:**
```
Reviewer rejects row with reason
  → _distill_rule(run_id, reason)  # LLM compresses to ≤200-char generic rule
  → append_learned_rule(rule)       # writes bullet to SKILL.md ## Learned rules
  → next run reads it via prompt 22 {{learned_rules}}
```

**Safety guards on rule writes:**
- Max `_MAX_RULES_PER_RUN = 5` rules appended per run
- Max 200 chars per rule
- No `##` or `<!--` allowed in rule text (prevents SKILL.md structural corruption)

---

## 7. State Schema — Interview Fields

Defined in `backend/domain/state.py`:

```python
topic_name:            str                    # user-typed topic label → slug → output folder name
interview_outcomes:    List[str]              # e.g. ["rag_evaluation_metrics", "prompt_injection_defense"]
interview_candidates:  List[Dict[str, Any]]   # raw harvested rows from connectors
interview_rows:        List[Dict[str, Any]]   # verified/published rows → the MD table
interview_iteration:   int                    # current research round (0–3)
interview_queued:      List[Dict[str, Any]]   # under-evidenced rows sent to human gate
interview_decisions:   Dict[str, Any]         # {row_id: {action: approve|edit|reject, reason?, question?}}
```

No reducers — all fields are last-writer-wins (single-branch flow, no parallel nodes).

---

## 8. Frontend Components

| File | Role |
|---|---|
| `frontend/src/components/InterviewTable.jsx` | Queue review UI: renders `interview_queued` rows; per-row approve / edit / reject with required reason on reject |
| `frontend/src/components/PipelineStepper.jsx` | Interview-specific progress lane: Assemble → Outcomes → Harvest → Verify → Review → Done; hides Set 1/Set 2 |
| `frontend/src/lib/pipelineState.js` | Sets `isInterview` flag; drives stepper variant |
| `frontend/src/hooks/useAgentRun.js` | Uses gate key `"interview"` (not `"classroom"`) for SSE resume |
| `frontend/src/pages/Generate.jsx` | 4th workflow button ("Mock Interview"); renders results as flat Markdown table; suppresses classroom SVG diagram |

---

## 9. Output Files

**Path pattern:**
```
generated_quizzes/<course_slug>/<topic_slug>/mock_interview/
  ├── mock_interview.md    ← GFM table, human-readable
  └── mock_interview.json  ← raw rows for reload / downstream tooling
```

**`mock_interview.md` columns:**

| # | Interview Question | Outcome | Companies | # Companies | Source links |
|---|---|---|---|---|---|

Sorted by `# Companies` descending. One row per published question.

**`mock_interview.json` row schema:**
```json
{
  "status":      "published",
  "question":    "...",
  "outcome":     "rag_evaluation_metrics",
  "companies":   [{"name": "Anthropic", "proof_url": "https://..."}],
  "source_urls": ["https://...", "https://..."],
  "first_seen":  "2026-06-25T...",
  "last_seen":   "2026-06-25T...",
  "run_ids":     ["run_abc123"]
}
```

---

## 10. Configuration & Settings

All in `backend/settings.py` (loaded from `.env`):

| Setting | Default | Purpose |
|---|---|---|
| `tavily_api_key` | `""` | Tavily search connector — blank disables it |
| `github_token` | `""` | Optional GitHub PAT — lifts rate limit 60 → 5000/hr |
| `interview_src_tavily_enabled` | `True` | Toggle Tavily connector |
| `interview_src_github_enabled` | `True` | Toggle GitHub connector |
| `interview_src_reddit_enabled` | `False` | Reddit connector (needs app credentials) |
| `interview_dedup_similarity` | `0.84` | Cosine threshold for embedding dedup + clustering |
| `interview_min_sources` | `2` | Independent domains required to auto-publish |
| `interview_research_rounds` | `3` | Max re-search rounds for under-evidenced groups |
| `tavily_max_results` | `6` | Results per Tavily API query |
| `interview_github_repos` | 26 repos | `owner/repo` strings — license-clean, company-tagged |
| `interview_source_allowlist` | 67 domains | Domains Tavily may search across |

---

## 11. Security Measures

| Measure | Where | Detail |
|---|---|---|
| SSRF guard | `sources/base.py:is_safe_public_url()` | Blocks RFC-1918, loopback, 169.254.x.x, multicast before any fetch |
| Prompt injection | `mock_interview.py:_one_line()` | Scraped text collapsed to 1 line, max 320 chars, before entering prompts 21/22 |
| Live-check cap | `_MAX_LIVE_CHECK_URLS = 200` | Bounds URL-resolution fan-out per run |
| SKILL.md rule cap | `_MAX_RULES_PER_RUN = 5` | Prevents runaway SKILL.md growth |
| Rule content guard | `interview_skill.py:append_learned_rule()` | Rejects rules with `##` or `<!--` (structural injection), max 200 chars |
| GitHub path validation | `github_repo.py` | `_REPO_RE` + `_PATH_RE` fullmatch — blocks traversal, URL encoding tricks |
| Tavily allowlist | `sources/tavily_search.py:_on_allowlist()` | DENY all if allowlist is empty or domain not listed |
| `follow_redirects=False` | `_link_alive()` | Redirect chain not followed during link-resolution (SSRF defence) |

---

## 12. File Map

| File | Role |
|---|---|
| `backend/agent/mock_interview.py` | All 5 pipeline nodes + evidence engine + helper functions |
| `backend/agent/interview_skill.py` | SKILL.md read/write API |
| `backend/agent/sources/base.py` | `Record`, `Connector` protocol, SSRF guard, `polite_get`, `enabled_connectors` |
| `backend/agent/sources/github_repo.py` | GitHub REST API connector |
| `backend/agent/sources/tavily_search.py` | Tavily search connector + `search_question()` for research loop |
| `backend/agent/prompts/20_interview_outcomes.md` | Prompt: name interview-relevant outcomes from session content |
| `backend/agent/prompts/21_interview_harvest.md` | Prompt: filter raw candidates to genuine on-topic questions |
| `backend/agent/prompts/22_interview_verify.md` | Prompt: ground evidence, report only supported companies |
| `backend/agent/graph.py` | LangGraph: nodes wired, `_route_after_assemble` fork |
| `backend/agent/nodes.py` | Node wrappers (assemble reuse) |
| `backend/agent/run.py` | `get_result()` — returns interview-specific fields for frontend |
| `backend/agent/export.py` | Output layout config |
| `backend/agent/llm.py` | Template validation fix (prevents `{{...}}` prompt injection) |
| `backend/domain/state.py` | `interview_*` state fields |
| `backend/memory.py` | Interview bank persistence (`("interview_bank", course, topic_slug)` namespace, dedup-on-write at 0.88) |
| `backend/api/agent.py` | `POST /api/agent/run` — accepts `workflow="mock_interview"` |
| `backend/settings.py` | All interview settings + source allowlists |
| `frontend/src/components/InterviewTable.jsx` | Queue review UI |
| `frontend/src/components/PipelineStepper.jsx` | Interview pipeline lane |
| `frontend/src/lib/pipelineState.js` | `isInterview` flag |
| `frontend/src/hooks/useAgentRun.js` | Gate key "interview" |
| `frontend/src/pages/Generate.jsx` | 4th workflow button, flat table rendering |
| `.claude/skills/verifying-interview-evidence/SKILL.md` | Live hard checks + auto-growing learned rules |
| `.claude/specs/10-mock-interview.md` | Full feature contract and sourcing spec |
| `.claude/plan/feature-11-mock-interview.md` | Step-by-step build plan (Parts 1–3) |
| `scripts/check_sources.py` | Source health diagnostic (checks allowlist domains) |
| `docs/dev-history/nxtmock_feature.txt` | Development log — fixes applied during implementation |
| `generated_quizzes/.../mock_interview/` | Output: `mock_interview.md` + `.json` |
