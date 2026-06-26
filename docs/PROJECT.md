# Agentic Interview Question Generator

## Problem

Educators and placement teams manually curate interview questions for Gen AI and LLM Application courses. This involves cross-referencing 1,700+ real company interview questions against 1,800+ curriculum questions across 45 sessions — a process that is slow, inconsistent, and starts from scratch every time. There's no feedback loop, so the same curation mistakes repeat across sessions.

## Solution

A single LLM agent that, given a session name, autonomously finds and assembles a set of 5–15 relevant interview questions. The agent has access to tools — it reads the session material, searches a pre-indexed question bank, generates questions when the bank falls short, validates relevance, and submits the final set for human review. The human approves or rejects each question before it goes to Google Sheets.

The key word is **autonomously**. The agent decides what to search for, when to generate new questions, when quality is sufficient, and when to submit. Python code only executes the tools — it doesn't make workflow decisions.

## How It Works

```
User selects session(s) on the web UI
         |
         v
   Agent receives goal + 11 tools
         |
         v
   Step 1: understand_session
           Reads session reading material, extracts learning outcomes,
           maps to Knowledge Points from curriculum, determines if
           session is theory-heavy or code-heavy
         |
         v
   Step 2: search_question_bank (×3-5 calls)
           Searches 3,248 pre-indexed questions using TF-IDF similarity
           Uses KP labels as search queries — not generic keywords
           Post-filters results by session scope
         |
         v
   Step 3: generate_interview_questions (if bank has gaps)
           LLM generates theory questions directly from learning outcomes
           Only used when the bank doesn't have enough matches
         |
         v
   Step 4: validate_relevance
           LLM checks every accumulated question against session outcomes
           Removes off-topic questions automatically
         |
         v
   Step 5: generate_coding_questions (if code-heavy session)
           Generates coding problems in portal format with starter code
         |
         v
   Step 6: Quality checks + dedup + generate answers
         |
         v
   Step 7: submit_question_set → Quality gate (LLM critique)
           If critique fails, agent revises and resubmits (max 2 rounds)
         |
         v
   Human reviews on web UI — accept/reject each question
         |
         v
   Approved questions → Google Sheets
```

The agent typically uses 10–14 tool calls per run. A hard budget cap of 20 prevents runaway costs.

## Knowledge Base

The agent works with three types of pre-prepared data, all stored as JSON files in the `data/` directory:

**Interview Questions** (`data/interview_questions.json`) — 3,133 real company interview questions filtered from a 36,000-row CSV. Only tech-relevant domains kept (Python, Flask, SQL, DSA, AI/ML, APIs, etc.). Each question has topic, sub-topic, difficulty, company attribution, and role context.

**Knowledge Graph** (`data/knowledge_graph.json`) — 106 Knowledge Points across 3 courses (Gen AI, LLM Applications, Flask), connected by 160 prerequisite edges forming a DAG. Each of the 45 sessions is mapped to its relevant KPs, learning outcomes, and session type. This lets the agent understand what a session teaches without making an LLM call.

**Scraped Questions** (`data/scraped_questions.json`) — 115 interview questions permanently extracted from 10 curated Gen AI interview websites. Scraped once, stored forever — no live scraping during generation.

These files are created by a one-time data preparation script (`scripts/prepare_data.py`) that filters the raw CSV, builds the knowledge graph from curriculum JSONs and reading materials, and scrapes the curated URLs.

## Agent Architecture

The agent is a single tool-use loop — not a multi-agent framework, not a pipeline of sequential LLM calls. It's one LLM conversation where the model decides which tools to call and in what order.

```
┌─────────────────────────────────────────────────┐
│                  AGENT LOOP                      │
│                                                  │
│  System prompt (goal + rules + tool list)        │
│  User prompt ("Generate for session X")          │
│                                                  │
│  while tool_calls < 20:                          │
│    response = LLM(messages, tools)               │
│    for each tool_call in response:               │
│      result = execute_tool(tool_call)            │
│      append result to conversation               │
│      emit SSE progress event                     │
│    if agent called submit_question_set:           │
│      run quality gate (LLM critique)             │
│      if pass or max revisions: break             │
│      else: feed critique back, continue          │
│                                                  │
│  return curated questions for human review        │
│                                                  │
└─────────────────────────────────────────────────┘
```

**AgentState** holds all accumulated questions, coding questions, code snippets, and session context across tool calls. Tools mutate this state. The LLM sees compact summaries of tool results — full data lives in Python.

**Context management**: Tool results are trimmed to 1,500 chars. Conversation history is capped at 24 turns. System + first user message are always preserved.

## Tools (11)

| Tool | What It Does | LLM Call? |
|------|-------------|-----------|
| `understand_session` | Extracts learning outcomes and KPs from session material | Uses knowledge graph first (instant), LLM only as fallback |
| `search_question_bank` | TF-IDF similarity search over 3,248 pre-indexed questions | No — pure Python (scikit-learn) |
| `generate_interview_questions` | Generates theory questions from learning outcomes | Yes |
| `validate_relevance` | Checks each question against session outcomes, removes mismatches | Yes |
| `generate_coding_questions` | Generates coding problems with starter code in portal format | Yes |
| `generate_expected_answers` | Generates answer outlines for questions missing them | Yes |
| `check_difficulty_balance` | Reports Easy/Medium/Hard distribution | No — pure Python |
| `check_outcome_coverage` | Reports which outcomes are covered vs missing | No — pure Python |
| `deduplicate_questions` | TF-IDF cosine similarity dedup (threshold 0.85) | No — pure Python (scikit-learn) |
| `remove_question` | Drops a specific question by ID | No — state mutation |
| `submit_question_set` | Finalizes set, triggers quality gate | Quality gate uses LLM |

## Data Preparation

Raw data sources are transformed into agent-ready JSON by `scripts/prepare_data.py`:

**Interview CSV → `data/interview_questions.json`**
- Input: 36,079 rows from `Interview Intelligence Master_ 2026 - Master Sheet.csv`
- Filtering: Keep only tech-relevant topics (Python, SQL, AI/ML, APIs, DSA, etc.). Drop aptitude, grammar, logical reasoning, soft skills.
- Output: 3,133 questions with `id`, `content`, `topic`, `sub_topic`, `difficulty`, `company`, `role`, `tech_stack`

**Curriculum JSONs → `data/knowledge_graph.json`**
- Input: 3 curriculum files (1,247 + 525 + 47 questions) with Knowledge Point mappings and prerequisite edges
- Processing: Extract 106 unique KPs, 160 prerequisite edges, parse 45 sessions from reading materials, map sessions to KPs
- Output: Knowledge graph with `knowledge_points` (label, course, prerequisites, dependents), `sessions` (KP IDs, outcomes, type), `prerequisite_edges`

**Curated URLs → `data/scraped_questions.json`**
- Input: 10 interview question URLs from `curated_urls.md`
- Processing: Scrape each URL once, LLM extracts questions with topic and difficulty
- Output: 115 permanent questions, no live scraping needed at runtime

## Question Output Format

Questions follow the Nxtmock portal format:

**Theory Questions** (QuestionDetails tab):
`question_id | category | content | topic | sub_topic | difficulty | asked_in_company | source | kp_label | expected_answer | feedback`

**Coding Questions** (CodingQuestion tab):
`id | category | title | content | code_id | topic | difficulty | language | source`

Where `content` is a concise plain-text problem statement (not heavy markdown), and `code_id` links to a separate **CodeSnippet** with the starter code template.

**CodeSnippet** (CodeSnippet tab):
`code_id | code_content | Language`

## Quality Assurance

Quality is enforced at three levels:

**Tool-level filtering** — `search_question_bank` post-filters results against session scope keywords. Questions with zero overlap to learning outcomes are dropped before the agent sees them.

**LLM relevance validation** — `validate_relevance` makes a separate LLM call (temperature 0.0) that evaluates every question against the session's learning outcomes. Off-topic questions are removed automatically.

**Submission quality gate** — When the agent calls `submit_question_set`, a critique LLM call checks the full set for relevance, difficulty balance, duplicates, and count. If the critique fails, the agent receives specific fix instructions and revises (up to 2 rounds). Force-passes after max revisions with a warning.

**Human review** — The final gate. Each question has Accept/Reject buttons with per-question feedback. Rejected questions are removed. The set only goes to Google Sheets after explicit human approval.

## Tech Stack

- **LLM**: Claude Haiku 4.5 (testing) / Sonnet (production) via OpenRouter
- **Agent loop**: OpenRouter tool_use with the `openai` Python SDK
- **Search**: scikit-learn TF-IDF with cosine similarity (ngram range 1-2)
- **Knowledge graph**: networkx for prerequisite DAG traversal
- **Data models**: Pydantic v2
- **Caching**: SQLite for session resolution cache, run history, RLHF feedback
- **Web UI**: Flask + Jinja2 + Server-Sent Events for live progress
- **Output**: Google Sheets via gspread + OAuth
- **Data prep**: pandas for CSV processing, BeautifulSoup for URL scraping

## Project Structure

```
app.py                              # Flask web app (3 pages)
scripts/
  prepare_data.py                   # One-time data preparation script
data/
  interview_questions.json          # 3,133 filtered interview questions
  knowledge_graph.json              # 106 KPs, 45 sessions, 160 edges
  scraped_questions.json            # 115 questions from curated URLs
src/
  agent.py                          # Agent loop: AgentState + run_agent()
  tools.py                          # 11 tool schemas + implementations
  prompts.py                        # Agent system prompt
  session_understanding.py          # Knowledge graph → SessionContext
  question_bank.py                  # TF-IDF retriever over JSON data
  orchestrator.py                   # Progress events + delegates to agent
  llm_client.py                     # OpenRouter client
  models.py                         # Pydantic models
  data_loader.py                    # Loads prepared JSON data files
  memory.py                         # SQLite: cache, history, feedback
  config.py                         # Paths, model selection, constraints
  sheets_writer.py                  # Google Sheets export
  utils/web.py                      # URL scraping utility
templates/
  index.html                        # Session selector (multi-select)
  progress.html                     # Live agent tool-call log (SSE)
  review.html                       # Per-question accept/reject
eval/
  eval_sets.json                    # 25 good + 20 bad questions for validation
```

## Constraints

- 5–15 questions per session
- Max 20 tool calls per agent run
- Coding questions only when session demands it (code-heavy or mixed)
- Human approval required before Google Sheets write
- All LLM calls go through OpenRouter, not direct API
- Testing model: Claude Haiku 4.5 (~$0.01/run)
- Production model: Claude Sonnet (~$0.17/run)

## RLHF Feedback Loop

Human feedback from the review page is stored in SQLite. Over time:
- Questions consistently rated "Remove" get added to a suppress list
- Questions rated "Good" get boosted in future runs
- Rejection reasons are tracked for pattern analysis

This creates a learning loop where the system improves with each generation cycle.
