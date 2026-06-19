"""Build comprehensive eval sets for all 45 sessions.

Preserves existing hand-written evals, generates lightweight evals
for remaining sessions from knowledge graph KP labels.
Adds coding question evals (good + bad) + format rules.
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
KG_PATH = PROJECT_ROOT / "data" / "knowledge_graph.json"
EVAL_PATH = PROJECT_ROOT / "eval" / "eval_sets.json"


def main():
    with open(KG_PATH, "r", encoding="utf-8") as f:
        kg = json.load(f)

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)

    existing_map = {s["session_name"]: s for s in existing["eval_sessions"]}
    kps = kg["knowledge_points"]

    all_sessions = []

    for name, info in sorted(kg["sessions"].items()):
        course = info.get("course", "unknown")
        stype = info.get("session_type", "mixed")
        kp_ids = info.get("kp_ids", [])
        outcomes = info.get("learning_outcomes", [])

        kp_labels = [kps[k]["label"] for k in kp_ids if k in kps]
        if not outcomes and kp_labels:
            outcomes = [f"Understand {l}" for l in kp_labels[:4]]

        session = {
            "session_name": name,
            "session_type": stype,
            "course": course,
            "kp_ids": kp_ids,
            "expected_outcomes": outcomes,
        }

        # ── Preserve existing hand-written evals ──
        if name in existing_map:
            ex = existing_map[name]
            old_good = ex.get("good_questions", [])
            old_bad = ex.get("bad_questions", [])

            if isinstance(old_good, dict):
                session["good_questions"] = old_good
            else:
                session["good_questions"] = {"theory": old_good, "coding": []}

            if isinstance(old_bad, dict):
                session["bad_questions"] = old_bad
            else:
                session["bad_questions"] = {"theory": old_bad, "coding": []}
        else:
            # ── Generate theory evals from KP labels ──
            good_theory = []
            diffs = ["Easy", "Medium", "Hard"]
            for i, label in enumerate(kp_labels[:3]):
                good_theory.append({
                    "content": f"Explain {label} and its practical applications.",
                    "difficulty": diffs[i % 3],
                    "why_good": f"Directly tests KP: {label}",
                })

            bad_theory = [
                {
                    "content": "What is programming?",
                    "bad_type": "too_generic",
                    "why_bad": "Too generic, not session-specific",
                },
            ]

            other_sessions = [n for n in kg["sessions"] if n != name]
            if other_sessions:
                other = other_sessions[len(name) % len(other_sessions)]
                bad_theory.append({
                    "content": f"Explain concepts from {other}.",
                    "bad_type": "off_topic",
                    "why_bad": f"About {other}, not {name}",
                })

            session["good_questions"] = {"theory": good_theory, "coding": []}
            session["bad_questions"] = {"theory": bad_theory, "coding": []}

        # ── Coding evals based on session type ──
        if stype in ("code_heavy", "mixed"):
            if not session["good_questions"].get("coding"):
                good_coding = []
                for label in kp_labels[:2]:
                    fn_name = label.lower().replace(" ", "_").replace("-", "_")[:30]
                    fn_name = "".join(c for c in fn_name if c.isalnum() or c == "_")
                    good_coding.append({
                        "title": label[:40] + " Implementation",
                        "content": f"Write a function that demonstrates {label}. The function should accept appropriate parameters and return a meaningful result.",
                        "starter_code": f"def {fn_name}():\n    # Write your code here\n    pass",
                        "difficulty": "Medium",
                        "why_good": f"Tests {label}, concise content, proper starter code",
                    })
                session["good_questions"]["coding"] = good_coding

            if not session["bad_questions"].get("coding"):
                session["bad_questions"]["coding"] = [
                    {
                        "title": "Generic Sort",
                        "content": "## Task\nImplement a sorting algorithm.\n## Input\n- A list of integers",
                        "bad_type": "wrong_format",
                        "why_bad": "Uses markdown headers instead of plain text. Generic DSA, not session-specific",
                    }
                ]

        elif stype == "theory_heavy":
            if not session["good_questions"].get("coding"):
                session["good_questions"]["coding"] = []
            if not session["bad_questions"].get("coding"):
                session["bad_questions"]["coding"] = [
                    {
                        "title": "Code Implementation",
                        "content": "Write code to implement concepts from this session.",
                        "bad_type": "wrong_session",
                        "why_bad": f"Theory-heavy session should not have coding questions",
                    }
                ]

        all_sessions.append(session)

    # ── Add any existing eval sessions NOT in knowledge graph ──
    kg_names = set(kg["sessions"].keys())
    for ex_name, ex_data in existing_map.items():
        if ex_name not in kg_names:
            old_good = ex_data.get("good_questions", [])
            old_bad = ex_data.get("bad_questions", [])

            session = {
                "session_name": ex_name,
                "session_type": ex_data.get("session_type", "mixed"),
                "course": ex_data.get("course", "unknown"),
                "kp_ids": [],
                "expected_outcomes": ex_data.get("expected_outcomes", []),
            }

            if isinstance(old_good, dict):
                session["good_questions"] = old_good
            else:
                session["good_questions"] = {"theory": old_good, "coding": []}

            if isinstance(old_bad, dict):
                session["bad_questions"] = old_bad
            else:
                session["bad_questions"] = {"theory": old_bad, "coding": []}

            all_sessions.append(session)
            print(f"  Preserved orphan eval: {ex_name}")

    # ── Count totals ──
    tgt = sum(len(s["good_questions"]["theory"]) for s in all_sessions)
    tbt = sum(len(s["bad_questions"]["theory"]) for s in all_sessions)
    tgc = sum(len(s["good_questions"].get("coding", [])) for s in all_sessions)
    tbc = sum(len(s["bad_questions"].get("coding", [])) for s in all_sessions)

    output = {
        "metadata": {
            "version": "3.0",
            "built_at": datetime.now().strftime("%Y-%m-%d"),
            "description": "Eval sets for all 45 sessions: theory + coding, good + bad, format rules",
            "total_sessions": len(all_sessions),
            "total_good_theory": tgt,
            "total_bad_theory": tbt,
            "total_good_coding": tgc,
            "total_bad_coding": tbc,
            "total_questions": tgt + tbt + tgc + tbc,
        },
        "eval_sessions": all_sessions,
        "format_rules": {
            "theory_question": {
                "required_fields": ["content", "difficulty", "topic", "source"],
                "content_rules": "Plain text question, clear and specific, tests one learning outcome",
                "difficulty_values": ["Easy", "Medium", "Hard"],
                "source_values": ["interview_db", "web", "generated"],
            },
            "coding_question": {
                "required_fields": ["title", "content", "code_id", "difficulty", "language"],
                "content_rules": "Plain text problem (1-4 sentences). NO markdown headers. Include sample I/O as plain text.",
                "starter_code_rules": "Separate CodeSnippet linked by code_id. Function signature + '# Write your code here'.",
                "category_format": "{LANGUAGE}_CODING (e.g., PYTHON_CODING)",
                "bad_format_examples": [
                    "Using ## headers in content",
                    "Embedding starter code inside content",
                    "Missing function signature",
                    "Category as LLM_APP_CODING instead of PYTHON_CODING",
                ],
            },
            "session_type_rules": {
                "theory_heavy": "0 coding questions expected",
                "code_heavy": "2-4 coding questions expected",
                "mixed": "1-2 coding questions expected",
            },
        },
    }

    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Eval sets for {len(all_sessions)} sessions:")
    print(f"  Good theory: {tgt}")
    print(f"  Bad theory:  {tbt}")
    print(f"  Good coding: {tgc}")
    print(f"  Bad coding:  {tbc}")
    print(f"  Total:       {tgt + tbt + tgc + tbc}")


if __name__ == "__main__":
    main()
