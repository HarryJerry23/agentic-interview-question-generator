import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Prepared data files (from scripts/prepare_data.py)
INTERVIEW_QUESTIONS_JSON = DATA_DIR / "interview_questions.json"
KNOWLEDGE_GRAPH_JSON = DATA_DIR / "knowledge_graph.json"

# Curriculum context (KP supplements — runtime, loaded by data_loader)
GEN_AI_JSON = DATA_DIR / "curriculum/gen_ai_final.json"
LLM_APPS_JSON = DATA_DIR / "curriculum/llm_applications_kp_links_final_fixed.json"
FLASK_JSON = DATA_DIR / "curriculum/flask_kp_links_final.json"
# Reading materials (runtime, used by session_understanding)
GEN_AI_RM = DATA_DIR / "reading_materials/gen_ai_reading_material.md"
LLM_APPS_RM = DATA_DIR / "reading_materials/llm_applications_reading_material.md"
# Precise per-session reading-material map (built by scripts/build_session_reading_material.py)
SESSION_MAP_JSON = DATA_DIR / "reading_materials/session_map.json"
# Raw source files (used by prepare_data.py only)
INTERVIEW_CSV = DATA_DIR / "raw/Interview Intelligence Master_ 2026 - Master Sheet.csv"
MEMORY_DB = PROJECT_ROOT / "memory.db"

# Model configuration
ENV = os.getenv("ENV", "development")  # development | staging | production

MODEL_CONFIG = {
    "development": "anthropic/claude-haiku-4-5",            # Cheap for testing
    "staging": "anthropic/claude-sonnet-4-6",
    "production": "anthropic/claude-sonnet-4-6",
}

LLM_MODEL = os.getenv("LLM_MODEL", MODEL_CONFIG.get(ENV, MODEL_CONFIG["development"]))

# Models selectable from the UI at runtime (OpenRouter ids). Extend as needed.
MODEL_OPTIONS = [
    {"id": "anthropic/claude-haiku-4-5",  "label": "Claude Haiku 4.5 · fast & cheap"},
    {"id": "anthropic/claude-sonnet-4-6", "label": "Claude Sonnet 4.6 · balanced"},
    {"id": "anthropic/claude-opus-4.1",   "label": "Claude Opus 4.1 · highest quality"},
    {"id": "openai/gpt-4o-mini",          "label": "GPT-4o mini · fast & cheap"},
    {"id": "openai/gpt-4o",               "label": "GPT-4o · balanced"},
]

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Question constraints
MIN_QUESTIONS = 5
MAX_QUESTIONS = 15
DEFAULT_DIFFICULTY_DISTRIBUTION = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
DEDUP_THRESHOLD = 0.85
QUALITY_PASS_THRESHOLD = 0.75
MAX_EVAL_RETRIES = 2
MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "20"))

# Live question harvesting (tools 12 & 13 — search_github_questions / search_web_questions)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")   # optional; raises GitHub API rate limit from 60→5000/hr
TAVILY_MAX_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "10"))

INTERVIEW_GITHUB_REPOS = [
    "llmgenai/LLMInterviewQuestions",
    "amitshekhariitbhu/ai-engineering-interview-questions",
    "amitshekhariitbhu/machine-learning-interview-questions",
    "Devinterview-io/llms-interview-questions",
    "shafaypro/CrackingMachineLearningInterview",
    "khangich/machine-learning-interview",
    "alirezadir/Machine-Learning-Interviews",
    "andrewekhalel/MLQuestions",
    "kojino/120-Data-Science-Interview-Questions",
    "youssefHosni/Data-Science-Interview-Questions-Answers",
    "rbhatia46/Data-Science-Interview-Resources",
    "Sroy20/machine-learning-interview-questions",
]

INTERVIEW_SOURCE_ALLOWLIST = {
    "tryexponent.com", "datalemur.com", "stratascratch.com", "prachub.com",
    "interviewquery.com", "prepfully.com", "igotanoffer.com", "glassdoor.com",
    "teamblind.com", "leetcode.com", "indeed.com", "interviewing.io",
    "hellointerview.com", "ambitionbox.com", "geeksforgeeks.org", "interviewbit.com",
    "prepinsta.com", "indiabix.com", "naukri.com", "reddit.com", "medium.com",
    "quora.com", "datascience.stackexchange.com", "stats.stackexchange.com",
    "stackoverflow.com", "datacamp.com", "analyticsvidhya.com", "kdnuggets.com",
    "towardsai.net", "towardsdatascience.com", "tredence.com", "igmguru.com",
    "vinsys.com", "novelvista.com", "generativeaimasters.in", "blockchain-council.org",
    "amquesteducation.com", "simplilearn.com", "edureka.co", "intellipaat.com",
    "projectpro.io", "turing.com", "springboard.com", "mlstack.cafe",
    "365datascience.com", "builtin.com",
    # Additional real-company interview-question sources
    "glassdoor.co.in", "careercup.com", "comparably.com", "fishbowlapp.com",
    "educative.io", "scaler.com", "levels.fyi", "ambitionbox.in",
    "tealhq.com", "interviewkickstart.com",
}
