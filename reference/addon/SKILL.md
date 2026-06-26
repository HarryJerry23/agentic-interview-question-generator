---
name: verifying-interview-evidence
description: The evidence-verification criteria the mock_interview verifier applies (Feature 11). Read by backend/agent/interview_skill.py — NOT a DB rubric. The "Learned rules" section self-evolves from reviewer rejections.
---

# Verifying interview-question evidence

These are the checks the `mock_interview` verify step applies to decide whether a harvested question is
a **real, attributable** interview question worth publishing. The model never authors a question or
invents a company — it only confirms what the evidence supports.

## Hard checks (a question must satisfy ALL to auto-publish)

1. **Real, not fabricated** — the question text appears (verbatim or near-verbatim) on a fetched source page.
2. **More than one independent source** — corroborated by **> 1 independent legitimate domain** (different
   sites/authors, not two pages of one site).
3. **Named company + resolving links** — at least one explicitly named company, and every cited link
   resolves (an anti-bot 401/403/429 still means the page exists; only 404/410/dead fails).
4. **Outcome-relevant** — maps to one of the topic's selected learning outcomes.
5. **Not a duplicate** — below the embedding-dedup threshold versus the published bank.
6. **Safe / appropriate** — genuinely an interview question; no PII, nothing offensive.

## Decision

- **Publish** — all hard checks pass.
- **Queue for human** — a genuine, on-topic question that is real but **under-evidenced** (e.g. only one
  independent source after the research loop, or a company named without a clearly supporting snippet).
- **Drop** — not a question, fabricated, off-topic, or no live source.

## Learned rules
<!-- Auto-appended from reviewer rejections (append_learned_rule). Each bullet sharpens the checks above
     so fewer weak candidates reach the human over time. Do not delete the header. -->
- Questions must cite a specific named company where the interview question was actually asked.
