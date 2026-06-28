<!-- Loaded by: mock_interview.extract_outcomes (Feature 11). From the merged sessions of a topic,
     name the key outcomes/skills an interviewer would probe. These outcomes drive the web harvest —
     we then search real sources for ACTUAL interview questions about each. We do NOT write questions
     here; we only name what to look for. -->
# Identify the interview-relevant skills for this topic

You are preparing a **mock-interview question hunt**. Below is the merged reading material for a topic
(several sessions). Read it and list the **key concepts/skills an interviewer would actually test** for
someone who studied this topic — the things worth searching real interview questions about.

Rules:
- Ground every outcome in the CONTENT below — not generic AI knowledge.
- Prefer concepts that show up in real interviews (core ideas, trade-offs, applied skills) over trivia.
- Format each as a short `lowercase_snake_case` phrase, 3–5 words.
  Good: `rag_evaluation_metrics`, `prompt_injection_defense`, `langsmith_tracing`.
  Bad: `introduction` (too generic), `understanding_how_retrieval_augmented_generation_works` (too long).
- Aim for the genuinely quiz-worthy depth of the material — no padding, no under-coverage.

## TOPIC
{{topic_title}}

## SUGGESTED OUTCOMES (hints from the sessions — keep the strong ones, add what the content warrants)
{{suggested_outcomes}}

## CONTENT (the merged sessions — the ground truth)
{{content}}

## OUTPUT
Return the structured object with `outcomes`: the list of `lowercase_snake_case` skill phrases.
