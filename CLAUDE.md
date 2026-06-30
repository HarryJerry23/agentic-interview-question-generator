# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic Interview Question Generator — a multi-agent pipeline that curates **real** interview questions for course sessions. It reads each session's reading material, resolves it to learning outcomes + Knowledge Points, retrieves real questions from a pre-indexed bank, GitHub interview repos, and Tavily web search, then validates, deduplicates, and assembles a question set. A human reviews before Google Sheets export.

**Architecture**: A 4-agent pipeline (Understanding → Retrieval → Validation → Evaluation) followed by an LLM quality gate, driven via OpenRouter tool_use. A React SPA (served by Flask) shows live progress and a per-question review screen. **Question generation is disabled — only real, sourced questions are used.**

## How It Works

```
User selects a topic → all its sessions/units are passed in →
  Understanding agent: understand_session (per-session reading material → outcomes, KPs) →
  Retrieval agent: search_question_bank (interview data first) → search_web_questions
    (Tavily, real company-attributed) → search_github_questions (supplemental) →
  Validation agent: validate_relevance (lenient) + deduplicate_questions →
  Evaluation agent: difficulty/coverage checks → generate_expected_answers →
    (coding Qs only if code-heavy) → submit_question_set →
  Quality gate (LLM critique; up to 2 revision rounds) →
Human reviews (React UI, per-question accept/reject) →
  Approve → Google Sheets | Reject → distil feedback into learned rules + re-generate
```

## Project Structure

```
app.py                              # Flask: JSON API + serves React SPA (frontend/dist); legacy Jinja fallback
frontend/                           # React SPA (Vite). Pages: SessionSelector, Progress, Review, History
  src/components/QuestionCard.jsx   # Per-question review card (shows honest attribution)
  src/pages/Progress.jsx            # Live tool log; auto-redirects to Review on completion
scripts/
  prepare_data.py                   # One-time: CSV→JSON, build knowledge graph, eval sets
  build_session_reading_material.py # Build data/reading_materials/session_map.json (per-session content)
data/
  interview_questions.json          # 1,509 company-attributed interview questions
  knowledge_graph.json              # KPs + sessions + prerequisite edges
  course_structure.json             # Topic → list of sessions (units); drives UI selection
  reading_materials/session_map.json# Canonical session name → that session's reading material
  reading_materials/*.md            # Source course reading materials (gen_ai, llm_applications)
  curriculum/*.json                 # KP-mapped curriculum questions (catalog source)
src/
  pipeline.py                       # AgentPipeline.run — orchestrates the 4 agents + quality gate
  agents/                           # UnderstandingAgent, RetrievalAgent, ValidationAgent, EvaluationAgent
  agent.py                          # AgentState, PipelineResult, _critique_question_set (quality gate)
  tools.py                          # Tool schemas + implementations (generation tool is blocked)
  prompts.py                        # Legacy single-agent prompt (deprecated); per-agent prompts live in agents/
  session_understanding.py          # Per-session resolution + merge → SessionContext (RM-first, KG fallback)
  question_bank.py                  # TF-IDF retriever over interview_questions.json
  sources/tavily_search.py          # Tavily web search + URL-based company extraction
  sources/github_repo.py            # GitHub interview-repo fetch (REST API)
  orchestrator.py                   # SSE progress queue + run_pipeline wrapper
  llm_client.py                     # OpenRouter client (chat + JSON extraction)
  models.py                         # Pydantic models; QuestionDetail.attribution (honest company-or-source)
  data_loader.py                    # Loads prepared JSON + per-session reading material (exact lookup)
  memory.py                         # SQLite: session cache, run history, RLHF learned rules
  config.py                         # Model selection, paths, constraints, Tavily/GitHub source lists
  sheets_writer.py                  # Google Sheets export (OAuth)
eval/
  eval_sets.json                    # Good/bad questions for validation
```

## Question Sources (real only — no generation)

| Source | Tool | Company attribution |
|--------|------|---------------------|
| Pre-indexed bank (1,509 Qs) | `search_question_bank` (TF-IDF) | Yes (verified) |
| Tavily web (56-domain allowlist) | `search_web_questions` | Best-effort from URL |
| GitHub interview repos | `search_github_questions` | No |
| `generate_interview_questions` | **BLOCKED** | — |

When a question has no real company, the output shows an **honest source label** (Glassdoor / GeeksforGeeks / AI-generated / the host domain) via `QuestionDetail.attribution` — never a blank or fabricated company.

## Reading Material → Relevance

`data/reading_materials/session_map.json` (built by `scripts/build_session_reading_material.py`) maps each canonical session name to ONLY that session's reading material. `data_loader.get_session_content` does exact + normalized lookup (no fuzzy substring fallback). `understand_session` resolves each selected session from its own content and merges, so multi-session topics get accurate, on-topic outcomes → sharper retrieval queries.

## Tech Stack

- **LLM**: Claude Haiku 4.5 (dev) / Sonnet (prod) via OpenRouter (`openai` SDK with tool_use)
- **Search**: scikit-learn TF-IDF (bank) + Tavily API (web) + GitHub REST API
- **Knowledge graph**: networkx DAG for prerequisite ordering
- **Data models**: Pydantic v2 (field validators + computed fields)
- **Cache/History**: SQLite (session resolutions, run history, RLHF learned rules)
- **Web**: Flask JSON API + React SPA (Vite, react-router); SSE for live progress
- **Output**: gspread + google-auth-oauthlib (Google Sheets via OAuth)
- **Data prep**: pandas (CSV)

## Key Constraints

- 5–15 questions per session
- Max tool calls bounded per agent (cost control)
- Question generation is DISABLED — only real, sourced questions
- No live scraping (offline scraping removed entirely)
- Retrieval order: interview bank first, then Tavily web, then GitHub
- Coding questions only for code-heavy sessions
- Human approval required before Google Sheets write
- Reject → distils feedback into learned rules + re-generates with same sessions
- Session understanding uses the per-session reading material first, knowledge graph as fallback
- Quality gate critiques the final set; agent revises up to 2 rounds
