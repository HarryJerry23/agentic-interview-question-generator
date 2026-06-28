# reconciling-specs — reference

## Classification legend

| Symbol | Meaning | Action |
|---|---|---|
| ✅ matches | Doc agrees with the code | Leave unchanged |
| ⚠️ drifted | Doc describes something different from the code | Reword doc to match code |
| ❌ not implemented | Documented as built, but absent from code (not future) | Remove or relocate to a clearly-future section |
| 🔭 explicitly future | Labelled planned/future/roadmap | Preserve; tidy labelling only |

## Spec / plan → implementation mapping

Use this to find the code that proves or disproves each documented claim.

| Doc area | Doc file(s) | Verify against |
|---|---|---|
| System overview, feature scope, future work | `specs/00-overview-and-build-plan.md` | `README.md`, overall repo; **Module Quiz / MCQ Practice = future (🔭)** |
| Architecture, topology, memory/state model | `specs/01-architecture.md` | `backend/agent/graph.py`, `backend/memory.py`, `backend/settings.py` |
| Data model | `specs/02-data-model.md` | `backend/domain/models.py`, `state.py` |
| Ingestion & session memory | `specs/03-ingestion-and-session-memory.md` | `backend/ingestion/*`, `backend/memory.py` |
| Evaluation rubric (30 checkpoints) | `specs/04-evaluation-rubric.md` | `backend/domain/rubric_seed.py`, `scoring.py` |
| Agents & workflow (nodes, prompts, variants) | `specs/05-agents-and-workflow.md` | `backend/agent/graph.py`, `nodes.py`, `rubric.py`, `variants.py`, `prompts/01…13` |
| Classroom quiz flow, gates, learning loop | `specs/06-classroom-quiz-flow.md` | `backend/agent/nodes.py`, `rubric.py`, `feedback.py`, prompt files |
| API & frontend | `specs/07-api-and-frontend.md` | `backend/api/*`, `frontend/src/pages/*`, `lib/api.js`, `lib/pipelineState.js` |
| Infra & deployment | `specs/08-infra-and-deployment.md` | `requirements.txt`, `backend/settings.py`, `backend/agent/cost.py`, `observability.py`, `.env.example` |
| Acceptance criteria | `specs/09-acceptance-criteria.md` | All of the above (does each criterion correspond to real behavior?) |
| Feature 1 — ingestion | `plan/feature-01-data-ingestion.md` | `backend/ingestion/*` |
| Feature 2 — content API + frontend | `plan/feature-02-content-api-frontend.md` | `backend/api/content.py`, `frontend/src/pages/ContentLibrary.jsx` |
| Feature 3 — agentic generation | `plan/feature-03-agentic-generation.md` | `backend/agent/nodes.py`, prompts 01–05, graph gate 1 |
| Feature 4 — rubric critic | `plan/feature-04-rubric-critic.md` | `backend/agent/rubric.py`, `feedback.py`, prompts 06–10 |
| Feature 5 — variants generation | `plan/feature-05-variants-generation.md` | `backend/agent/variants.py`, `export.py`, `cost.py`, prompts 11–13 |

## Specific facts worth spot-checking (from current code)

- **3 human gates** (generation, rubric, variants) in `graph.py`.
- **13 prompts**, files `01_split_session.md` … `13_variant_briefing.md`.
- **8 variant types** — `backend/agent/variants.py::VARIANT_TYPES`.
- **30-checkpoint rubric** — `backend/domain/rubric_seed.py` + deterministic `scoring.py`.
- **4 React pages** — ContentLibrary, Generate, RubricView, History.
- **Future scope (preserve as 🔭):** Module Quiz, MCQ Practice.

If any count above no longer matches the code, that's drift (⚠️) — report it, don't assume the doc is right.

## Reporting tip

Order the drift table by status severity (❌ then ⚠️ then 🔭 then ✅), and give a one-line tally:
"`X matches · Y drifted · Z not-implemented · W future`". Then ask which corrections to apply.
