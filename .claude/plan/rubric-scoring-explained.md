# How quiz questions are graded

> What it means for a question to "pass", how the grade is decided, why you can trust it, and how
> this relates to the system's memory.

---

## 1. What passing means

Every generated question is graded against a fixed checklist of **30 quality rules** — things like
"the question is clear", "the wrong options are believable", "the marked answer is actually correct",
"it teaches understanding, not memorisation".

The grading is **strict and all-or-nothing**: a question **passes (green)** only if it meets **every**
rule that applies to it. Miss even one and it **fails (red)**. There is no middle ground and no
"good enough" — green or red, nothing in between.

A red question isn't thrown away. The system first tries to fix it automatically, and if it still
can't, a human reviewer is asked to decide.

---

## 2. Who decides, and why it's reliable

Two steps, with a clear division of labour:

1. **An AI reviewer reads each question and lists what's wrong** — it returns only the rules the
   question *breaks* (for example: "the wrong options are too obviously wrong"). It does not award a
   score.
2. **Simple, fixed arithmetic turns that list into the verdict** — if the AI listed any broken rule,
   the question is red; if the list is empty, it's green.

This split is what makes the result trustworthy. The verdict itself is plain arithmetic, so it is
**exact and repeatable** — the same question with the same findings always gets the same grade. The
only judgement call is *which rules a question breaks*, and that is handled in the next point.

---

## 3. How good is the AI reviewer at catching wrong answers?

This is measured, not assumed. The system includes a checker that takes real questions, deliberately
**breaks the answer key** (marks a wrong option as correct), and asks the AI reviewer to grade both
the good and the broken versions. A reliable reviewer should pass the good ones and fail the broken
ones.

Across 4 sessions and 26 deliberately-broken questions, the reviewer caught the wrong answer **100%
of the time**, and never wrongly failed a good question (**0% false alarms**) — even when the
explanation that would normally give the answer away was removed, forcing it to check against the
source material.

The reviewer also follows an explicit instruction to **work out the correct answer itself from the
reading material first**, then compare that to the marked answer and flag a mismatch.

To run the checker yourself:
```bash
python -m backend.agent.critic_eval --course <course> --session <session> --hard
```

---

## 4. What happens if the AI reviewer fails to respond

AI calls can occasionally time out or return something unreadable. The system is built so that this
can **never let a bad question slip through as "passed"**:

- it tries the reviewer **once more**;
- if it still gets nothing usable, the question is marked **red and sent to a human** with the note
  *"could not be evaluated — needs review"*.

So uncertainty always lands on the safe side — a question is never quietly passed just because the
reviewer didn't answer.

---

## 5. Does the "memory" feature change the grade? No.

The system has a memory that learns from reviewers' corrections (see *How the system learns*). It is
natural to wonder whether that memory affects the grade. It does not.

Memory plays a **supporting** role: it stores the checklist of rules, and it feeds the AI reviewer
helpful reminders learned from past corrections. But the **pass/fail verdict is always decided by the
AI's findings plus the fixed arithmetic** — never by memory. Memory shapes what the system pays
attention to *next time*; it never overrides this question's grade.

---

## 6. Summary

- A question passes only if it meets **all** applicable quality rules — one miss makes it red.
- The grade is fixed arithmetic over an AI reviewer's findings, so it's exact and repeatable.
- The reviewer reliably catches wrong answers (measured at 100%, with no false alarms), and when it
  can't evaluate something, that question goes to a human rather than being passed.
- The memory feature supports the reviewer but never decides the grade.

---

## Where this lives in the code

| Piece | Location |
|---|---|
| The grading arithmetic (strict pass/fail) | `backend/domain/scoring.py` → `score_question` |
| The 30 rules and their categories | `backend/domain/rubric_seed.py` |
| The AI reviewer + retry/fail-safe | `backend/agent/rubric.py` → `_run_critic_batch` |
| The reviewer's instructions | `backend/agent/prompts/07_rubric_critic.md` |
| The accuracy checker | `backend/agent/critic_eval.py` |

Quick checks:
```bash
python -m backend.domain.scoring     # confirms the pass/fail arithmetic (offline, instant)
python -m backend.agent.critic_eval --course building_llm_applications --session integrating_mcp --hard
```
