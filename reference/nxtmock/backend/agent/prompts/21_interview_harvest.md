<!-- Loaded by: mock_interview.harvest (Feature 11). The candidates below were pulled VERBATIM from
     real interview-question sources. Your job is to KEEP only the ones that are genuine interview
     questions relevant to one of the topic outcomes, and tag each kept item with its best-matching
     outcome. You do NOT write, rephrase, or invent questions — only select and tag by index. -->
# Filter harvested candidates to genuine, on-topic interview questions

Below is a numbered list of candidate strings scraped from real interview-question sources, and the
list of this topic's outcomes. Decide which candidates are **real interview questions** that map to one
of the outcomes.

Keep a candidate only if ALL hold:
- It is genuinely an **interview question** (a question or a clear "explain/describe/implement…" task),
  not a heading, navigation text, section title, or fragment.
- It is **relevant to one of the OUTCOMES** below (about this topic's concepts/skills).
- It is self-contained enough to pose to a candidate.

Do not invent or reword. Just select by index and assign the single best-matching outcome.

## OUTCOMES
{{outcomes}}

## CANDIDATES
{{candidates}}

## OUTPUT
Return the structured object with `items`: one entry per candidate you KEEP, each with
`index` (the candidate's number), `outcome` (the matching `lowercase_snake_case` outcome), and
`keep: true`. Omit candidates you reject.
