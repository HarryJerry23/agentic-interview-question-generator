# checking-correctness — reference

## Scoring rubric (total 10 points)

Score each category, then sum. Round the overall to 1 decimal.

| Category | Weight | What full marks means |
|---|---|---|
| Imports & deprecations | 2.5 | No deprecated/renamed/removed symbols; all import paths match the latest docs. |
| API signatures | 2.5 | Every function/method call matches current parameter names, order, and return shapes. |
| Recommended patterns | 2.0 | Uses the idioms the latest docs recommend; no superseded patterns. |
| Version currency | 1.5 | Pinned versions are current stable (or intentionally, defensibly behind). |
| Types & contracts | 1.5 | Pydantic models / typed state / data contracts match current library expectations. |

**Deductions within a category** (guidance, not rigid): −0.5 per confirmed outdated usage,
−1.0 per deprecated symbol still in use, −0.25 per "works but no longer recommended" pattern.
Never deduct for something you could not verify against a fetched doc — flag it as "unverified" instead.

A category cannot go below 0. Overall = sum of category scores.

## Doc-source routing table

| Library (as pinned) | Primary source | Tool call |
|---|---|---|
| langgraph, langgraph-checkpoint, langgraph-checkpoint-postgres | LangChain docs MCP | `search_docs_by_lang_chain` → `query_docs_filesystem_docs_by_lang_chain` |
| langchain, langchain-openai | LangChain docs MCP | same as above |
| flask, flask-cors | Context7 | `resolve-library-id("flask")` → `query-docs` |
| psycopg | Context7 | `resolve-library-id("psycopg")` → `query-docs` |
| pydantic-settings, pydantic | Context7 | `resolve-library-id("pydantic-settings")` → `query-docs` |
| tiktoken, openpyxl, python-dotenv | Context7 | `resolve-library-id` → `query-docs` |
| react, react-dom | Context7 | `resolve-library-id("react")` → `query-docs` |
| react-router-dom | Context7 | `resolve-library-id("react-router")` → `query-docs` |
| vite, @vitejs/plugin-react | Context7 | `resolve-library-id("vite")` → `query-docs` |
| @xyflow/react | Context7 | `resolve-library-id("xyflow")` → `query-docs` |
| react-markdown, rehype-*, remark-gfm, highlight.js | Context7 | `resolve-library-id` → `query-docs` |
| "latest stable version of X?" / release notes | Web | `WebSearch` then `WebFetch` official docs/changelog |

If a Context7 / LangChain MCP lookup returns nothing useful, fall back to `WebSearch` + `WebFetch`
of the official documentation site. Never invent an API from memory — cite a fetched source.

## Where to look in this project (usage hotspots)

| Subsystem | Files | Latest-docs questions to ask |
|---|---|---|
| LangGraph graph & gates | `backend/agent/graph.py`, `nodes.py`, `rubric.py`, `variants.py`, `practice.py`, `module.py` | StateGraph construction, `interrupt`/resume, conditional edges (3-way `_route_after_assemble`: classroom/practice/module_quiz). |
| Workflows & prompts | `backend/agent/module.py` (Feature 9), prompts `18_module_plan`/`19_module_generate`; the `present_labels` label-neutral loops in `variants.py` | New `module_quiz` workflow merges sessions → variants tail; verify the merged-assemble + label-neutral generalization against current LangGraph state/reducer patterns. |
| Checkpointer / store / memory | `backend/agent/graph.py`, `backend/memory.py` | `PostgresSaver` / `PostgresStore` setup + `.setup()`, connection pooling. |
| LLM client | `backend/agent/llm.py` | langchain-openai client init, model kwargs. |
| Embeddings / ingestion | `backend/ingestion/*`, `backend/agent/*` | OpenAIEmbeddings, tiktoken chunking. |
| Settings | `backend/settings.py` | pydantic-settings v2 `BaseSettings` import + `SettingsConfigDict`. |
| API | `backend/api/app.py`, `agent.py`, `content.py`, `rubric.py` | Flask 3 app/blueprint patterns, flask-cors, SSE streaming. |
| Frontend | `frontend/src/**` | React 18 idioms, react-router v6 APIs, @xyflow/react v12 API, react-markdown v9 props. |

## Example report skeleton

```
## Dependency inventory
| Library | Pinned | Used in |
|---|---|---|
| langgraph | >=0.2.50 | backend/agent/graph.py, run.py |
...

## Findings
### langgraph (latest: X.Y.Z)
- backend/agent/graph.py:42 — uses `Foo.bar(...)`; latest docs replace with `Foo.baz(...)`
  (https://langchain-ai.github.io/langgraph/...). Severity: deprecated.

## Scorecard
Overall: 8.5 / 10
- Imports & deprecations: 2.0 / 2.5
- API signatures: 2.5 / 2.5
- Recommended patterns: 1.5 / 2.0
- Version currency: 1.0 / 1.5
- Types & contracts: 1.5 / 1.5

## To reach 10/10 (prioritized)
1. [deprecated] backend/agent/graph.py:42 — replace `Foo.bar` with `Foo.baz` (cite). 
2. [version] bump langgraph >=0.2.50 → latest stable to pick up <reason>.
...
```
