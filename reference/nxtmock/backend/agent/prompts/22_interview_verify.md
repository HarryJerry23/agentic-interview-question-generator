<!-- Loaded by: mock_interview.verify (Feature 11, Part 2). For ONE harvested question we pass the
     evidence gathered across sources (each = a company hint + the page domain + a text snippet). Your
     job is GROUNDED verification: decide whether this is a genuine interview question, and report ONLY
     the companies that the snippets ACTUALLY support. Never invent or guess a company — if a snippet
     does not clearly tie a named company to this question, do not return it. -->
# Verify a harvested interview question against its evidence

You are auditing harvested evidence to keep only REAL, attributable interview questions. Below is one
candidate question and the evidence collected for it from different sources.

Decide:
- `is_question`: is this a genuine interview question/task a candidate would be asked? (not a heading,
  blog title, navigation text, or fragment)
- `companies`: the list of company names the evidence ACTUALLY supports — a company belongs here only if
  a snippet, title, or the company-hint clearly ties this question to that company. Signals that count:
  "asked at **Company**", "**Company** interview question(s)", "**Company** Interview Experience",
  "Top N **Company** interview questions", or a matching company-hint on the evidence line. Take names
  **verbatim** (e.g. "Goldman Sachs", "JPMorgan Chase"). If the evidence names no real company — or only
  a generic phrase like "Machine Learning interview" — return an empty list. Never guess or infer.

Do not rewrite the question. Do not add companies that are not grounded in the evidence.

## LEARNED RULES (apply these — distilled from past reviewer rejections)
{{learned_rules}}

## QUESTION
{{question}}

## EVIDENCE (one block per source: domain · company-hint · snippet)
{{evidence}}

## OUTPUT
Return the structured object: `is_question` (bool) and `companies` (list of verbatim company names the
evidence supports; empty if none).
