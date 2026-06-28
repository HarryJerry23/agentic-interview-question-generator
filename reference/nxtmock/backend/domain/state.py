"""QuizState — the single LangGraph state for the generation workflow + its reducers.

Parallel branches (one per set) write disjoint slices, so the collection fields use commutative
reducers (02 §3). Everything else is last-writer-wins. Nodes return DELTA-ONLY dicts.
"""
from __future__ import annotations

from typing import Annotated, Any, Dict, List, TypedDict

from backend.domain.models import Question


# ── Reducers (commutative + associative; branches own disjoint keys) ─────────────

def merge_questions_by_qid(cur: List[Question], upd: List[Question]) -> List[Question]:
    """Upsert by qid → regenerate (same qid) replaces in place; no duplicates/orphans."""
    d = {q.qid: q for q in cur}
    d.update({q.qid: q for q in upd})
    return list(d.values())


def merge_dict(cur: Dict[str, Any], upd: Dict[str, Any]) -> Dict[str, Any]:
    return {**cur, **upd}


def merge_iteration(cur: Dict[str, int], upd: Dict[str, int]) -> Dict[str, int]:
    """Scoped, max-merge → parallel set branches never clobber each other's round counter."""
    out = dict(cur)
    for k, v in upd.items():
        out[k] = max(out.get(k, 0), v)
    return out


class QuizState(TypedDict, total=False):
    """All fields the split→plan→generate→concept-check→refine→accept flow uses."""
    run_id: str
    course: str
    session: str
    session_title: str
    workflow: str                                      # "classroom_quiz" | "mcq_practice" | "module_quiz"

    # module_quiz (Feature 9) — merges several sessions into one body (label "module"); `session`
    # holds the slugified module_name as the run/export identity, `sessions` the selected ids.
    sessions: List[str]                                # selected session ids to merge (module_quiz only)
    module_name: str                                   # reviewer-typed name → identity/folder/History
    module_sessions: List[Dict[str, Any]]              # per-session [{title,text,outcomes}] for ≥6/session planning

    # assemble
    content_ref: str                                   # f"{course}/{session}"
    sections: List[Dict[str, Any]]                     # [{idx, heading, text, token_count}]
    course_outcomes: List[str]

    # coding detection (Feature 7) — gates whether code-analysis/FIB variants are produced
    is_coding: bool                                    # session contains real code
    code_languages: List[str]                          # detected languages, most-frequent first
    primary_language: str                              # the language to author code variants in

    # split / plan  — keyed by set_label ("set_a"|"set_b"); merged per-set
    set_plan: Annotated[Dict[str, Any], merge_dict]    # {set_label: SetPlan-as-dict}

    # generate / refine
    questions: Annotated[List[Question], merge_questions_by_qid]

    # concept-check
    outcome_checks: Annotated[Dict[str, Any], merge_dict]   # {qid: OutcomeCheck-as-dict}
    iteration: Annotated[Dict[str, int], merge_iteration]   # {set_label: round}

    # human gate (generation) / feedback
    human_decisions: Dict[str, Any]                    # {qid: HumanDecision-as-dict}
    feedback_written: List[str]                        # generic rule sentences persisted this run
    accepted: List[Dict[str, Any]]                     # generation-accepted (intermediate)
    dropped: List[Dict[str, Any]]
    needs_attention: List[Dict[str, Any]]

    # ── Rubric phase (Feature 4) — runs after the generation gate, in the same run ──
    rubric_questions: Annotated[List[Question], merge_questions_by_qid]  # the working set being scored
    critic_scores: Annotated[Dict[str, Any], merge_dict]   # {qid: CriticScore-as-dict}
    briefings: Dict[str, Any]                          # {qid: {summary, suggested_fix}} for the gate
    rubric_iteration: int                              # evaluate⟲optimize rounds run
    flagged_for_human: List[str]                       # qids still failing after the loop
    rubric_decisions: Dict[str, Any]                   # {qid: RubricDecision-as-dict}
    rubric_approved: List[Dict[str, Any]]              # final survivors → handed to the variants phase
    rubric_rejected: List[Dict[str, Any]]
    rubric_summary: Dict[str, Any]                     # {green, red, approved, rejected, edited}
    promoted_checkpoints: List[str]                    # checkpoint ids auto-refined this run

    # ── Variants phase (Feature 5) — runs after the rubric gate, in the same run ──
    variants: Annotated[List[Question], merge_questions_by_qid]  # generated variants (base_question_keys → base)
    variant_scores: Annotated[Dict[str, Any], merge_dict]   # {variant_qid: CriticScore-as-dict} (per-question)
    set_variant_scores: Dict[str, Any]                 # {set_label: per-set score dict (4.x / 1.4)}
    variant_briefings: Dict[str, Any]                  # {variant_qid: {summary, suggested_fix}} for the gate
    variant_iteration: int                             # evaluate⟲optimize rounds run on variants
    variant_decisions: Dict[str, Any]                  # {variant_qid: VariantDecision-as-dict}
    variants_approved: List[Dict[str, Any]]            # approved variants → exported
    variants_rejected: List[Dict[str, Any]]
    variant_summary: Dict[str, Any]                    # {green, red, approved, rejected, total}
    exported: List[Dict[str, Any]]                     # export_set/zip/report results (paths + counts)

    # ── MCQ Practice phase (Feature 8) — replaces the variants phase when workflow == "mcq_practice"
    practice_summary: Dict[str, Any]                   # {approved, total, types: {type: count}}

    # ── Mock Interview (Feature 11) — harvest REAL interview questions; never generated.
    # No parallel branches in this flow, so these are plain last-writer-wins (no reducers needed).
    topic_name: str                                    # reviewer-typed topic identity (slug → folder/History)
    interview_outcomes: List[str]                      # key outcomes/skills the harvest targets
    interview_candidates: List[Dict[str, Any]]         # raw harvested rows {question, company, source_url, ...}
    interview_rows: List[Dict[str, Any]]               # verified/published rows → the md table
    interview_iteration: int                           # verify⟲research rounds (Part 2)
    interview_queued: List[Dict[str, Any]]             # under-evidenced rows awaiting human review (Part 3)
    interview_decisions: Dict[str, Any]                # {row_id: {action: approve|edit|reject, ...}} (Part 3)

    status: str                                        # running | awaiting_human | done | error


MAX_REFINE_ROUNDS = 3      # hard cap (concept-check ↔ refine)
MIN_REFINE_ROUNDS = 2      # always run concept-check at least twice before accepting
MAX_RUBRIC_ROUNDS = 2      # evaluate ⟲ optimize: at most this many scoring rounds
MAX_VARIANT_ROUNDS = 2     # variant evaluate ⟲ optimize: at most this many scoring rounds
