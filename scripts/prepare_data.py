"""Data Preparation Script — transforms raw sources into agent-ready JSON files.

Run once: python scripts/prepare_data.py

Outputs:
  data/interview_questions.json  — filtered interview questions from CSV
  data/knowledge_graph.json      — KPs + session mapping + prerequisites
  data/scraped_questions.json    — questions extracted from curated URLs
  eval/eval_sets.json            — updated evaluation sets
"""

import sys
import os
import json
import uuid
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

DATA_DIR = PROJECT_ROOT / "data"
EVAL_DIR = PROJECT_ROOT / "eval"


# ═══════════════════════════════════════════════════════════════════════════
# PART 1: Interview CSV -> Filtered JSON
# ═══════════════════════════════════════════════════════════════════════════

# Topics to KEEP (tech-relevant domains)
KEEP_TOPICS = {
    "PYTHON", "FLASK", "DJANGO", "FASTAPI",
    "SQL", "SQL_QUERYING", "DATABASE", "NOSQL", "MONGODB",
    "DSA", "DATA_STRUCTURES", "ALGORITHMS", "ARRAYS", "LINKED_LIST",
    "TREES", "GRAPHS", "SORTING", "SEARCHING", "DYNAMIC_PROGRAMMING",
    "API", "API_DESIGN", "REST", "REST_APIS", "HTTP", "HTTP_METHODS",
    "OOP", "OBJECT_ORIENTED_PROGRAMMING", "CLASSES", "INHERITANCE",
    "JAVASCRIPT", "REACT", "REACT_JS", "NODE", "NODEJS", "EXPRESS",
    "MACHINE_LEARNING", "AI", "AI_ML", "GEN_AI", "GENERATIVE_AI",
    "AGENTIC_AI", "LLM", "NLP", "DEEP_LEARNING", "NEURAL_NETWORKS",
    "AUTHENTICATION", "SECURITY", "OAUTH",
    "DEPLOYMENT", "DOCKER", "CI_CD", "DEVOPS", "CLOUD",
    "TESTING", "UNIT_TESTING", "INTEGRATION_TESTING",
    "GIT", "VERSION_CONTROL",
    "FULL_STACK_DEVELOPMENT", "BACKEND", "FRONTEND",
    "PERFORMANCE_OPTIMIZATION", "CACHING", "SCALING",
    "CS_BASICS", "PROGRAMMING_LANGUAGES", "MEMORY_MANAGEMENT",
    "ERROR_HANDLING", "DEBUGGING", "LOGGING",
    "DESIGN_PATTERNS", "SYSTEM_DESIGN", "MICROSERVICES",
    "DATA_HANDLING", "DATA_MANIPULATION", "PANDAS", "NUMPY",
    "HOOKS", "STATE_MANAGEMENT", "COMPONENT_LIFECYCLE",
    "PROJECT_DISCUSSION", "INTRODUCTION",
}

# Question types to KEEP
KEEP_TYPES = {"THEORY", "CODING", "PROJECT", "CONCEPTUAL", "GENERAL"}

# Topics to explicitly DROP
DROP_TOPICS = {
    "APTITUDE", "LOGICAL_REASONING", "VERBAL_REASONING",
    "QUANTITATIVE_APTITUDE", "GRAMMAR", "READING_COMPREHENSION",
    "VOCABULARY", "ENGLISH", "SOFT_SKILLS", "COMMUNICATION",
    "PUZZLES", "RIDDLES", "BRAIN_TEASERS",
}


def prepare_interview_questions():
    """Convert interview CSV to filtered, structured JSON."""
    csv_path = PROJECT_ROOT / "Interview Intelligence Master_ 2026 - Master Sheet.csv"
    if not csv_path.exists():
        print("  ERROR: Interview CSV not found")
        return

    print("  Loading CSV...")
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    total_original = len(df)
    print(f"  Loaded {total_original} rows")

    # Detect columns
    q_text_col = next((c for c in df.columns if c.strip() == "Question"), None)
    q_uuid_col = next((c for c in df.columns if "UUID" in str(c)), None)
    q_type_col = next((c for c in df.columns if "Question Type" in str(c)), None)
    company_col = next((c for c in df.columns if "Company Name" in str(c)), None)
    role_col = next((c for c in df.columns if c.strip() == "Role"), None)
    tech_col = next((c for c in df.columns if "Tech Stack" in str(c)), None)
    topic_col = next((c for c in df.columns if c == "topic"), None)
    sub_topic_col = next((c for c in df.columns if c == "sub_topic"), None)
    diff_col = next((c for c in df.columns if "difficulty" in c.lower()), None)

    if not q_text_col:
        print("  ERROR: Question column not found")
        return

    diff_map = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard"}
    questions = []
    skipped_reasons = {"empty": 0, "url": 0, "short": 0, "type": 0, "topic": 0}

    for _, row in df.iterrows():
        content = str(row.get(q_text_col, "")).strip()

        # Skip empty/invalid
        if not content or content == "nan":
            skipped_reasons["empty"] += 1
            continue
        if content.startswith("http"):
            skipped_reasons["url"] += 1
            continue
        if len(content) < 20:
            skipped_reasons["short"] += 1
            continue

        # Get metadata
        q_type = str(row.get(q_type_col, "")).strip().upper() if q_type_col else ""
        topic = str(row.get(topic_col, "")).strip().upper() if topic_col and pd.notna(row.get(topic_col)) else ""
        sub_topic = str(row.get(sub_topic_col, "")).strip().upper() if sub_topic_col and pd.notna(row.get(sub_topic_col)) else ""

        # Filter by question type
        if q_type and q_type not in KEEP_TYPES and q_type != "":
            # Allow BEHAVIORAL/SELF_INTRODUCTION only if topic is tech-relevant
            if topic not in KEEP_TOPICS:
                skipped_reasons["type"] += 1
                continue

        # Filter by topic — WHITELIST mode: keep only if topic OR sub_topic is in KEEP_TOPICS
        topic_match = topic in KEEP_TOPICS or sub_topic in KEEP_TOPICS
        # Also check if any KEEP word appears as substring (catches "MACHINE_LEARNING" in "ML_BASICS" etc)
        if not topic_match:
            combined_topic = f"{topic}_{sub_topic}"
            topic_match = any(k in combined_topic for k in ["PYTHON", "FLASK", "SQL", "API", "HTTP",
                "OOP", "DSA", "ALGORITHM", "DATA_STRUCT", "JAVASCRIPT", "REACT",
                "MACHINE_LEARN", "AI", "GEN_AI", "LLM", "NLP", "DEEP_LEARN",
                "DOCKER", "DEPLOY", "GIT", "TEST", "AUTH", "DATABASE",
                "DESIGN_PATTERN", "SYSTEM_DESIGN", "MICRO", "CODING",
                "HOOK", "STATE_MANAGE", "COMPONENT", "FRONTEND", "BACKEND"])
        if not topic_match:
            skipped_reasons["topic"] += 1
            continue

        # Get other fields
        q_id = str(row.get(q_uuid_col, "")).strip() if q_uuid_col else ""
        if not q_id or q_id == "nan":
            q_id = str(uuid.uuid4())

        difficulty = diff_map.get(str(row.get(diff_col, "")).strip().upper(), "Medium") if diff_col else "Medium"
        company = str(row.get(company_col, "")).strip() if company_col and pd.notna(row.get(company_col)) else None
        role = str(row.get(role_col, "")).strip() if role_col and pd.notna(row.get(role_col)) else None
        tech_stack = str(row.get(tech_col, "")).strip() if tech_col and pd.notna(row.get(tech_col)) else None

        if company == "nan":
            company = None
        if role == "nan":
            role = None
        if tech_stack == "nan":
            tech_stack = None

        questions.append({
            "id": q_id,
            "content": content,
            "question_type": q_type if q_type else "GENERAL",
            "topic": topic if topic else "GENERAL",
            "sub_topic": sub_topic if sub_topic else None,
            "difficulty": difficulty,
            "company": company,
            "role": role,
            "tech_stack": tech_stack,
        })

    output = {
        "metadata": {
            "source": "Interview Intelligence Master_ 2026 - Master Sheet.csv",
            "total_original": total_original,
            "total_filtered": len(questions),
            "filtered_at": datetime.now().isoformat(),
            "skipped": skipped_reasons,
        },
        "questions": questions,
    }

    out_path = DATA_DIR / "interview_questions.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Written {len(questions)} questions to {out_path}")
    print(f"  Skipped: {skipped_reasons}")


# ═══════════════════════════════════════════════════════════════════════════
# PART 2: Knowledge Graph — KPs + Session Mapping + Prerequisites
# ═══════════════════════════════════════════════════════════════════════════

def prepare_knowledge_graph():
    """Build knowledge graph from curriculum JSONs + reading materials."""

    # Load all curriculum JSONs
    json_files = [
        (PROJECT_ROOT / "gen_ai_final.json", "gen_ai"),
        (PROJECT_ROOT / "llm_applications_kp_links_final_fixed.json", "llm_applications"),
        (PROJECT_ROOT / "flask_kp_links_final.json", "flask"),
    ]

    all_kps = {}       # kp_id -> {label, course, prerequisites, dependents}
    all_edges = []     # [{from, to}]
    kp_question_count = {}  # kp_id -> count of questions using it

    for filepath, course_name in json_files:
        if not filepath.exists():
            print(f"  WARNING: {filepath.name} not found")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        questions = data.get("questions", [])
        print(f"  {filepath.name}: {len(questions)} questions")

        for q in questions:
            # Extract KPs
            for kp in q.get("selected_knowledge_points", []):
                kp_id = kp["resolved_kp_id"]
                kp_label = kp["resolved_kp_label"]

                if kp_id not in all_kps:
                    all_kps[kp_id] = {
                        "label": kp_label,
                        "course": course_name,
                        "prerequisites": [],
                        "dependents": [],
                    }

                kp_question_count[kp_id] = kp_question_count.get(kp_id, 0) + 1

            # Extract edges
            for edge in q.get("selected_prerequisite_edges", []):
                src = edge.get("source_resolved_kp_id", "")
                tgt = edge.get("target_resolved_kp_id", "")
                if src and tgt:
                    all_edges.append({"from": src, "to": tgt})

    # Deduplicate edges
    edge_set = set()
    unique_edges = []
    for e in all_edges:
        key = (e["from"], e["to"])
        if key not in edge_set:
            edge_set.add(key)
            unique_edges.append(e)

    # Build prerequisite/dependent links
    for edge in unique_edges:
        src, tgt = edge["from"], edge["to"]
        if src in all_kps and tgt not in all_kps[src].get("dependents", []):
            all_kps[src]["dependents"].append(tgt)
        if tgt in all_kps and src not in all_kps[tgt].get("prerequisites", []):
            all_kps[tgt]["prerequisites"].append(src)

    # Parse sessions from reading materials
    sessions = {}
    rm_files = [
        (PROJECT_ROOT / "gen_ai_reading_material.md", "gen_ai"),
        (PROJECT_ROOT / "llm_applications_reading_material.md", "llm_applications"),
    ]

    for rm_path, course_name in rm_files:
        if not rm_path.exists():
            continue
        text = rm_path.read_text(encoding="utf-8")
        # Remove code blocks
        clean = re.sub(r'```[\s\S]*?```', '', text)
        # Find session headings
        pattern = r'^"?#\s+([A-Z][^\n]+)'
        skip_titles = {"introduction", "common issues you may encounter",
                       "setting the scheduler to run every week"}

        for match in re.finditer(pattern, clean, re.MULTILINE):
            title = match.group(1).strip().strip('"').strip()
            if title.lower() in skip_titles:
                continue
            if re.match(r'^\d+\.', title):
                continue
            if len(title) < 8:
                continue

            sessions[title] = {
                "course": course_name,
                "session_type": "theory_heavy" if course_name == "gen_ai" else "code_heavy",
                "kp_ids": [],
                "learning_outcomes": [],
                "key_concepts": [],
            }

    # Map sessions -> KPs: keyword matching first, LLM for empty ones
    for session_name, session_data in sessions.items():
        session_lower = session_name.lower()
        for kp_id, kp_data in all_kps.items():
            if kp_data["course"] != session_data["course"]:
                continue
            kp_label_lower = kp_data["label"].lower()
            kp_words = set(w for w in kp_label_lower.split() if len(w) > 3)
            session_words = set(w for w in session_lower.split() if len(w) > 3)
            overlap = kp_words & session_words
            if len(overlap) >= 1:
                session_data["kp_ids"].append(kp_id)

    # Content-based mapping for sessions with 0 KP matches
    # Read RM content and match KP labels against it
    empty_sessions = [s for s, d in sessions.items() if not d["kp_ids"]]
    if empty_sessions:
        print(f"  {len(empty_sessions)} sessions need content-based KP mapping...")

        for session_name in empty_sessions:
            course = sessions[session_name]["course"]

            # Get reading material content for this session
            rm_path = None
            for p, c in rm_files:
                if c == course:
                    rm_path = p
                    break

            rm_content_lower = ""
            if rm_path and rm_path.exists():
                text = rm_path.read_text(encoding="utf-8")
                # Find session content (search for heading)
                idx = text.lower().find(session_name.lower()[:30])
                if idx >= 0:
                    rm_content_lower = text[idx:idx+4000].lower()

            if not rm_content_lower:
                rm_content_lower = session_name.lower()

            # Match KP labels against session content (broader matching)
            matched = []
            for kp_id, kp_data in all_kps.items():
                if kp_data["course"] != course:
                    continue
                kp_label_lower = kp_data["label"].lower()
                # Split into meaningful words (3+ chars)
                kp_words = [w for w in kp_label_lower.split() if len(w) > 3
                           and w not in {"with", "from", "that", "this", "using", "based"}]
                # Check if any KP word appears in session content
                matches = sum(1 for w in kp_words if w in rm_content_lower)
                if matches >= 1 and len(kp_words) > 0:
                    score = matches / len(kp_words)
                    matched.append((kp_id, score))

            # Sort by score, take top 5
            matched.sort(key=lambda x: -x[1])
            sessions[session_name]["kp_ids"] = [m[0] for m in matched[:5]]

            # Determine session type based on content
            if any(kw in rm_content_lower for kw in ["def ", "class ", "import ", "flask", "code", "function", "api"]):
                sessions[session_name]["session_type"] = "code_heavy"
            elif any(kw in rm_content_lower for kw in ["agent", "workflow", "build", "project"]):
                sessions[session_name]["session_type"] = "mixed"

            print(f"    {session_name}: {len(sessions[session_name]['kp_ids'])} KPs mapped")

    output = {
        "metadata": {
            "total_kps": len(all_kps),
            "total_edges": len(unique_edges),
            "total_sessions": len(sessions),
            "courses": ["gen_ai", "llm_applications", "flask"],
            "built_at": datetime.now().isoformat(),
        },
        "knowledge_points": all_kps,
        "sessions": sessions,
        "prerequisite_edges": unique_edges,
    }

    out_path = DATA_DIR / "knowledge_graph.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Written {len(all_kps)} KPs, {len(unique_edges)} edges, {len(sessions)} sessions to {out_path}")


# ═══════════════════════════════════════════════════════════════════════════
# PART 3: Scraped Questions — Curated URLs -> Permanent JSON
# ═══════════════════════════════════════════════════════════════════════════

def prepare_scraped_questions():
    """Scrape curated URLs once, extract questions via LLM, save as JSON."""
    out_path = DATA_DIR / "scraped_questions.json"
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        count = existing.get("metadata", {}).get("total_questions", 0)
        if count > 0:
            print(f"  Already scraped ({count} questions). Skipping.")
            return

    from src.utils.web import scrape_url
    from src.llm_client import chat_completion_json

    urls_path = PROJECT_ROOT / "curated_urls.md"
    if not urls_path.exists():
        print("  ERROR: curated_urls.md not found")
        return

    urls = [
        line.strip() for line in urls_path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("http")
    ]
    print(f"  Found {len(urls)} URLs to scrape")

    all_questions = []

    for url in urls:
        print(f"  Scraping: {url[:70]}...")
        text = scrape_url(url)
        if not text:
            print(f"    Failed to fetch")
            continue

        result = chat_completion_json(
            system_prompt="""Extract ALL interview questions from this webpage.

For each question return:
- question: full question text as a string
- topic: clean short topic label (2-4 words, e.g., "Prompt Engineering", "LLM Architecture")
- difficulty: "Easy", "Medium", or "Hard" (distribute as 30% Easy, 50% Medium, 20% Hard)
- category: one of GEN_AI, LLM, AI_ML, PYTHON, ML_OPS, PROMPT_ENGINEERING, RAG, AGENTS

Respond in JSON: {"questions": [{"question": "...", "topic": "...", "difficulty": "Medium", "category": "GEN_AI"}]}

Extract EVERY interview question. Do NOT include answers.""",
            user_prompt=f"Webpage content:\n{text}",
            max_tokens=4096,
        )

        questions = result.get("questions", [])
        count = 0
        for q in questions:
            q_text = q.get("question", "").strip()
            if not q_text or len(q_text) < 20:
                continue

            all_questions.append({
                "id": str(uuid.uuid4()),
                "content": q_text,
                "topic": q.get("topic", "General"),
                "difficulty": q.get("difficulty", "Medium"),
                "category": q.get("category", "GEN_AI"),
                "source_url": url,
            })
            count += 1

        print(f"    Extracted {count} questions")

    output = {
        "metadata": {
            "total_questions": len(all_questions),
            "total_urls": len(urls),
            "scraped_at": datetime.now().isoformat(),
        },
        "questions": all_questions,
    }

    out_path = DATA_DIR / "scraped_questions.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Written {len(all_questions)} questions to {out_path}")


# ═══════════════════════════════════════════════════════════════════════════
# PART 4: Updated Eval Sets
# ═══════════════════════════════════════════════════════════════════════════

def prepare_eval_sets():
    """Build evaluation sets for 5 sessions with good/bad question examples."""

    eval_data = {
        "metadata": {
            "version": "2.0",
            "built_at": datetime.now().isoformat(),
            "description": "Evaluation sets for validating agent question relevance and quality",
        },
        "eval_sessions": [
            {
                "session_name": "Exploring Gen AI Capabilities",
                "session_type": "theory_heavy",
                "course": "gen_ai",
                "expected_outcomes": [
                    "Understand real-time web browsing with AI tools",
                    "Use deep research capabilities across multiple sources",
                    "Interact with AI using voice input and output",
                    "Choose the right AI model for different tasks"
                ],
                "good_questions": [
                    {"content": "What is the difference between ChatGPT's web browsing and deep research features?", "difficulty": "Medium", "why_good": "Directly compares two capabilities taught in session"},
                    {"content": "When should you use voice interaction with AI instead of text-based prompts?", "difficulty": "Easy", "why_good": "Tests understanding of voice I/O use cases from session"},
                    {"content": "How does AI search differ from traditional search engines like Google?", "difficulty": "Easy", "why_good": "Core concept of session section 1.1"},
                    {"content": "What factors should you consider when choosing between ChatGPT, Claude, and Gemini for a task?", "difficulty": "Hard", "why_good": "Tests model selection criteria from session"},
                    {"content": "Explain how screen sharing capability can be used to get AI assistance.", "difficulty": "Medium", "why_good": "Tests specific capability covered in session 1.4"},
                ],
                "bad_questions": [
                    {"content": "What is zero-shot prompting?", "bad_type": "off_topic", "why_bad": "Prompt engineering is a different session"},
                    {"content": "Write a Python function to sort a list.", "bad_type": "wrong_category", "why_bad": "Coding question in a theory session about AI capabilities"},
                    {"content": "What is AI?", "bad_type": "too_generic", "why_bad": "Too basic, doesn't test session-specific content"},
                    {"content": "Explain the transformer architecture.", "bad_type": "off_topic", "why_bad": "LLM internals covered in a different session"},
                ],
            },
            {
                "session_name": "Prompt Engineering Fundamentals",
                "session_type": "theory_heavy",
                "course": "gen_ai",
                "expected_outcomes": [
                    "Understand the RCATF framework for prompt design",
                    "Write effective zero-shot and few-shot prompts",
                    "Structure prompts with role, context, action, tone, and format",
                    "Apply prompt engineering to improve LLM output quality"
                ],
                "good_questions": [
                    {"content": "What does RCATF stand for in prompt engineering?", "difficulty": "Easy", "why_good": "Tests core framework taught in session"},
                    {"content": "Rewrite 'Tell me about dogs' using the RCATF framework.", "difficulty": "Medium", "why_good": "Tests practical application of the framework"},
                    {"content": "What is the difference between zero-shot and few-shot prompting?", "difficulty": "Medium", "why_good": "Key comparison from session content"},
                    {"content": "Why is specifying the output format important in a prompt?", "difficulty": "Easy", "why_good": "Tests the Format component of RCATF"},
                    {"content": "Design a prompt for an LLM to act as a senior Python code reviewer.", "difficulty": "Hard", "why_good": "Tests role-setting and structured prompt design"},
                ],
                "bad_questions": [
                    {"content": "What is RAG?", "bad_type": "off_topic", "why_bad": "RAG is a separate, later session"},
                    {"content": "Explain how neural networks learn.", "bad_type": "off_topic", "why_bad": "Deep learning internals, not prompt engineering"},
                    {"content": "What is a database?", "bad_type": "too_generic", "why_bad": "Completely unrelated to prompting"},
                    {"content": "Build a multi-agent system.", "bad_type": "out_of_scope", "why_bad": "Agents covered in a later session"},
                ],
            },
            {
                "session_name": "Building LLM Applications using Python | Part 1",
                "session_type": "code_heavy",
                "course": "llm_applications",
                "expected_outcomes": [
                    "Set up Google Colab for LLM development",
                    "Configure Gemini API authentication using Colab Secrets",
                    "Build a Study Assistant application using Gemini LLM",
                    "Understand the three components of LLM apps: LLM brain, API connector, prompt"
                ],
                "good_questions": [
                    {"content": "What are the three essential components of an LLM application?", "difficulty": "Easy", "why_good": "Core concept from session"},
                    {"content": "How do you securely store API keys in Google Colab using Colab Secrets?", "difficulty": "Medium", "why_good": "Specific technique taught in session"},
                    {"content": "Write code to initialize a Gemini client and send a prompt.", "difficulty": "Medium", "why_good": "Coding question matching session's hands-on exercise"},
                    {"content": "What is the google-genai package and how is it used?", "difficulty": "Easy", "why_good": "Tests knowledge of specific tool from session"},
                    {"content": "Build a Study Assistant that takes a topic and returns an explanation using Gemini API.", "difficulty": "Hard", "why_good": "Tests the session's main project"},
                ],
                "bad_questions": [
                    {"content": "What is Flask?", "bad_type": "off_topic", "why_bad": "Flask is Part 2, not Part 1"},
                    {"content": "Explain Python list comprehensions.", "bad_type": "too_generic", "why_bad": "Generic Python, not LLM application specific"},
                    {"content": "What does range() do?", "bad_type": "too_generic", "why_bad": "Basic Python, not related to LLM apps"},
                    {"content": "Deploy an application to AWS.", "bad_type": "out_of_scope", "why_bad": "Deployment is a separate session"},
                ],
            },
            {
                "session_name": "Building LLM Applications using Python | Part 2",
                "session_type": "code_heavy",
                "course": "llm_applications",
                "expected_outcomes": [
                    "Build REST APIs with Flask",
                    "Handle GET and POST HTTP requests",
                    "Return JSON responses from Flask endpoints",
                    "Create a product CRUD API"
                ],
                "good_questions": [
                    {"content": "How do you define a route in Flask using @app.route()?", "difficulty": "Easy", "why_good": "Core Flask concept from session"},
                    {"content": "What is the difference between GET and POST methods in Flask?", "difficulty": "Medium", "why_good": "Key HTTP concept from session"},
                    {"content": "Write a Flask endpoint that returns a list of products as JSON.", "difficulty": "Medium", "why_good": "Matches session's product API exercise"},
                    {"content": "How do you access request body data in a Flask POST endpoint?", "difficulty": "Medium", "why_good": "Specific skill taught in session"},
                    {"content": "Implement a complete CRUD API for products using Flask.", "difficulty": "Hard", "why_good": "Tests the session's main project"},
                ],
                "bad_questions": [
                    {"content": "What is the Gemini API?", "bad_type": "off_topic", "why_bad": "Gemini is Part 1, not Part 2"},
                    {"content": "Explain Django ORM.", "bad_type": "out_of_scope", "why_bad": "Session uses Flask, not Django"},
                    {"content": "What is Python?", "bad_type": "too_generic", "why_bad": "Too basic for a Flask API session"},
                    {"content": "How does RAG work?", "bad_type": "off_topic", "why_bad": "RAG is a completely different session"},
                ],
            },
            {
                "session_name": "Introduction to Retrieval-Augmented Generation | Part 1",
                "session_type": "mixed",
                "course": "llm_applications",
                "expected_outcomes": [
                    "Understand RAG architecture and workflow",
                    "Explain vector embeddings and their role in retrieval",
                    "Implement document chunking using RecursiveCharacterTextSplitter",
                    "Use ChromaDB for vector storage and search"
                ],
                "good_questions": [
                    {"content": "What is Retrieval-Augmented Generation and why is it needed?", "difficulty": "Easy", "why_good": "Core definition from session"},
                    {"content": "Explain the three stages of a RAG pipeline: indexing, retrieval, generation.", "difficulty": "Medium", "why_good": "Tests understanding of full pipeline"},
                    {"content": "What is ChromaDB and how is it used in a RAG system?", "difficulty": "Medium", "why_good": "Specific tool from session"},
                    {"content": "How does RecursiveCharacterTextSplitter work in LangChain?", "difficulty": "Medium", "why_good": "Tests specific technique from session"},
                    {"content": "Write code to create a simple RAG pipeline using LangChain and ChromaDB.", "difficulty": "Hard", "why_good": "Coding question matching session content"},
                ],
                "bad_questions": [
                    {"content": "What is zero-shot prompting?", "bad_type": "off_topic", "why_bad": "Prompt engineering is a different session"},
                    {"content": "Explain Flask routing.", "bad_type": "off_topic", "why_bad": "Flask is a different session entirely"},
                    {"content": "What is AI?", "bad_type": "too_generic", "why_bad": "Not specific to RAG"},
                    {"content": "Build a multi-agent system.", "bad_type": "out_of_scope", "why_bad": "Multi-agent is a later session"},
                ],
            },
        ],
    }

    # Count totals
    total_good = sum(len(s["good_questions"]) for s in eval_data["eval_sessions"])
    total_bad = sum(len(s["bad_questions"]) for s in eval_data["eval_sessions"])
    eval_data["metadata"]["total_good_questions"] = total_good
    eval_data["metadata"]["total_bad_questions"] = total_bad

    out_path = EVAL_DIR / "eval_sets.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)

    print(f"  Written {total_good} good + {total_bad} bad questions across {len(eval_data['eval_sessions'])} sessions to {out_path}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    EVAL_DIR.mkdir(exist_ok=True)

    print("=" * 60)
    print("DATA PREPARATION")
    print("=" * 60)

    print("\n[1/4] Interview Questions (CSV -> JSON)...")
    prepare_interview_questions()

    print("\n[2/4] Knowledge Graph (KPs + Sessions + Prerequisites)...")
    prepare_knowledge_graph()

    print("\n[3/4] Scraped Questions (URLs -> JSON)...")
    print("  This requires LLM calls and may take 1-2 minutes...")
    try:
        prepare_scraped_questions()
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Skipping URL scraping — you can re-run later")

    print("\n[4/4] Eval Sets...")
    prepare_eval_sets()

    print("\n" + "=" * 60)
    print("DONE! Check the data/ and eval/ directories.")
    print("=" * 60)
