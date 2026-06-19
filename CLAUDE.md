# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic Interview Question Generator — a single LLM agent with 11 tools that autonomously curates interview questions for course sessions. The agent reads session material, searches a pre-indexed question bank, generates questions when the bank falls short, validates relevance, and assembles a question set — all through autonomous tool-use decisions, not hardcoded pipeline steps.

**Architecture**: Single agent with 11 tools, driving the workflow via OpenRouter tool_use/function calling. Knowledge graph resolves sessions to KPs without LLM calls. TF-IDF searches a 3,248-question bank. Human reviews before Google Sheets export.

## How It Works

```
User selects session(s) → Agent receives goal + tools →
  understand_session (from knowledge graph, no LLM) →
  search_question_bank (TF-IDF over 3,248 Qs) ×3-5 →
  generate_interview_questions (if bank has gaps) →
  validate_relevance (LLM checks each Q) →
  generate_coding_questions (portal format + starter code) →
  quality checks → submit → quality gate (LLM critique) →
Human reviews (Flask UI, per-question accept/reject) →
  Approve → Google Sheets | Reject → re-generate automatically
```

## Project Structure

```
app.py                              # Flask web app (input + progress + review)
scripts/
  prepare_data.py                   # One-time: CSV→JSON, build knowledge graph, scrape URLs
data/
  interview_questions.json          # 3,133 filtered interview questions
  knowledge_graph.json              # 106 KPs, 45 sessions, 160 prerequisite edges
  scraped_questions.json            # 115 questions from 10 curated URLs
src/
  agent.py                          # Core: agent loop (AgentState + run_agent + quality gate)
  tools.py                          # 11 tool schemas + implementations
  prompts.py                        # Agent system prompt (goal, rules, workflow, budget)
  session_understanding.py          # Knowledge graph → SessionContext (LLM fallback)
  question_bank.py                  # TF-IDF retriever over JSON data
  orchestrator.py                   # Thin wrapper: SSE progress events → agent
  llm_client.py                     # OpenRouter client (chat + JSON extraction)
  models.py                         # Pydantic models (GenerationConfig, QuestionDetail, etc.)
  data_loader.py                    # Loads prepared JSON data files
  memory.py                         # SQLite: session cache, run history, RLHF feedback
  config.py                         # Model selection, paths, constraints
  sheets_writer.py                  # Google Sheets export (OAuth)
  utils/web.py                      # URL scraping utility
templates/
  index.html                        # Session selector (multi-select + custom topic)
  progress.html                     # Live agent tool-call log (SSE, dark theme)
  review.html                       # Per-question accept/reject with feedback
eval/
  eval_sets.json                    # 25 good + 20 bad questions for validation
```

## Agent Tools (11)

| Tool | Type | LLM? |
|------|------|------|
| `understand_session` | Data | Knowledge graph first, LLM fallback |
| `search_question_bank` | Retrieval | No — TF-IDF (scikit-learn) |
| `generate_interview_questions` | Generation | Yes — from learning outcomes |
| `validate_relevance` | Quality | Yes — checks each Q against outcomes |
| `generate_coding_questions` | Generation | Yes — portal format + CodeSnippet |
| `generate_expected_answers` | Generation | Yes — answer outlines |
| `check_difficulty_balance` | Quality | No — Python counting |
| `check_outcome_coverage` | Quality | No — keyword overlap |
| `deduplicate_questions` | Quality | No — TF-IDF cosine similarity |
| `remove_question` | Curation | No — state mutation |
| `submit_question_set` | Terminal | Quality gate uses LLM critique |

## Data Files

| File | Contents |
|------|----------|
| `data/interview_questions.json` | 3,133 filtered questions (from 36K CSV) |
| `data/knowledge_graph.json` | 106 KPs + 45 sessions + 160 edges |
| `data/scraped_questions.json` | 115 questions from 10 curated URLs |
| `gen_ai_reading_material.md` | Gen AI session reading materials |
| `llm_applications_reading_material.md` | LLM Apps session reading materials |
| `gen_ai_final.json` | 1,247 Gen AI curriculum Qs with KP mappings |
| `llm_applications_kp_links_final_fixed.json` | 525 LLM Apps curriculum Qs |
| `flask_kp_links_final.json` | 47 Flask curriculum Qs |

## Tech Stack

- **LLM**: Claude Haiku 4.5 (dev) / Sonnet (prod) via OpenRouter (`openai` SDK with tool_use)
- **Search**: scikit-learn TF-IDF + cosine similarity over pre-indexed JSON
- **Knowledge graph**: networkx DAG for prerequisite ordering
- **Data models**: Pydantic v2 with field validators
- **Cache/History**: SQLite (session resolutions, run history, RLHF feedback)
- **Web UI**: Flask + Jinja2 + SSE (Server-Sent Events for live progress)
- **Output**: gspread + google-auth-oauthlib (Google Sheets via OAuth)
- **Data prep**: pandas (CSV), BeautifulSoup (URL scraping)

## Key Constraints

- 5-15 questions per session
- Max 20 tool calls per agent run (cost control)
- Coding questions only for code-heavy/mixed sessions (portal format + CodeSnippet)
- Human approval required before Google Sheets write
- Reject → re-generates with same sessions automatically (no homepage redirect)
- Session understanding uses knowledge_graph.json first (instant, no LLM cost)
- Quality gate critiques the final set; agent revises up to 2 rounds
