"""One-time script: filter interview_questions.json to AI-relevant questions only."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BANK_PATH = DATA_DIR / "interview_questions.json"

KEEP_PATTERNS = [
    "python", "flask", "ai", "ml", "machine_learn", "deep_learn", "neural",
    "llm", "nlp", "gen_ai", "generative", "agentic", "agent", "langchain",
    "rag", "retrieval", "embed", "vector", "transformer", "gpt", "prompt",
    "fine_tun", "conversational", "rest_api", "api_design", "api_integration",
    "deployment", "third_party", "large_language", "natural_language",
    "llm_applic", "llm_concept", "llm_integr", "ai_ml", "ai_integr",
    "ai_applic", "ai_tool", "ai_agent", "ai_ethic", "text_to_speech",
    "diffusion", "stable_diff", "image_gen", "audio_gen",
]

REMOVE_PATTERNS = [
    "react", "javascript", "node_js", "java", "css", "html", "bootstrap",
    "sql", "sqlite", "database", "dsa", "data_struct", "algorithm",
    "sorting", "searching", "dynamic_prog", "greedy", "backtrack",
    "logical_reason", "quantitative", "aptitude", "spring", "hibernate",
    "blockchain", "hooks", "component", "dom", "jquery", "redux",
    "typescript", "angular", "vue", "svelte", "webpack",
]

# For generic topic names, also scan content for non-AI tech keywords
# Content keywords — applied to ALL questions (not just generic topics)
CONTENT_REMOVE = [
    " react ", "reactjs", "react.js", "react hooks", "class component",
    "functional component", " jsx", " tsx", " angular", "vue.js", " svelte",
    " javascript ", "typescript", " jquery", "node.js", "nodejs",
    " java ", "spring boot", "hibernate", " sql ", "mysql", "postgresql",
    " mongodb", "mongoose", " django", "bootstrap css",
    "html element", "css class", "css selector", "dom element",
    "16gb ram", "ram usage", "memory management in os",
    "browser will", "open in browser", "save this file",
]

CONTENT_KEEP = [
    "ai ", "artificial intelligence", "machine learning", "deep learning",
    "llm", "language model", "neural network", "python", "flask",
    "langchain", "rag", "retrieval", "embedding", "vector store",
    "transformer", "gpt", "prompt", "fine-tun", " agent", "openai",
    "hugging face", "generative", "nlp", "natural language",
    "api endpoint", "rest api", "flask route",
]


def should_keep(q: dict) -> bool:
    topic = (q.get("topic") or "").lower()
    sub = (q.get("sub_topic") or "").lower()
    combined = topic + "_" + sub

    is_keep = any(p in combined for p in KEEP_PATTERNS)
    is_remove = any(p in combined for p in REMOVE_PATTERNS)

    if is_remove and not is_keep:
        return False

    # Content scan: remove questions with clear non-AI signals
    import re
    content = " " + (q.get("content") or "").lower() + " "
    # Word-boundary checks for common false-negative tech keywords
    has_react = bool(re.search(r'\breact\b|\breactjs\b', content))
    has_java = bool(re.search(r'\bjava\b', content)) and not bool(re.search(r'\bjavascript\b', content))
    has_oops = bool(re.search(r'\bpolymorphism\b|\binheritance\b|\bencapsulation\b', content)) and not any(
        ai_kw in content for ai_kw in ['python', 'ai ', 'llm', 'machine learning', 'agent']
    )
    has_ai_content = any(p in content for p in CONTENT_KEEP)
    has_nonai_content = has_react or has_java or has_oops or any(p in content for p in CONTENT_REMOVE)
    if has_nonai_content and not has_ai_content:
        return False

    return True


def main():
    with open(BANK_PATH) as f:
        data = json.load(f)

    questions = data.get("questions", [])
    kept = [q for q in questions if should_keep(q)]
    removed = len(questions) - len(kept)

    data["questions"] = kept
    data["metadata"]["total_filtered"] = len(kept)
    data["metadata"]["ai_filter_applied"] = True
    data["metadata"]["removed_non_ai"] = removed

    with open(BANK_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Done. Kept: {len(kept)}, Removed: {removed}, Total was: {len(questions)}")

    # Show top removed topics for verification
    from collections import Counter
    all_qs = questions
    removed_qs = [q for q in all_qs if not should_keep(q)]
    removed_topics = Counter(
        (q.get("topic", "") + "/" + (q.get("sub_topic") or ""))
        for q in removed_qs
    )
    print("\nTop removed topic/sub_topic pairs:")
    for t, c in removed_topics.most_common(15):
        print(f"  {c:4d}  {t}")


if __name__ == "__main__":
    main()
