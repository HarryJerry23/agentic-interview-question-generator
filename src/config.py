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
SCRAPED_QUESTIONS_JSON = DATA_DIR / "scraped_questions.json"

# Raw source files (used by prepare_data.py, not at runtime)
GEN_AI_JSON = PROJECT_ROOT / "gen_ai_final.json"
LLM_APPS_JSON = PROJECT_ROOT / "llm_applications_kp_links_final_fixed.json"
FLASK_JSON = PROJECT_ROOT / "flask_kp_links_final.json"
INTERVIEW_CSV = PROJECT_ROOT / "Interview Intelligence Master_ 2026 - Master Sheet.csv"
GEN_AI_RM = PROJECT_ROOT / "gen_ai_reading_material.md"
LLM_APPS_RM = PROJECT_ROOT / "llm_applications_reading_material.md"
CURATED_URLS = PROJECT_ROOT / "curated_urls.md"
MEMORY_DB = PROJECT_ROOT / "memory.db"

# Model configuration
ENV = os.getenv("ENV", "development")  # development | staging | production

MODEL_CONFIG = {
    "development": "anthropic/claude-haiku-4-5",           # Cheap for testing
    "staging": "anthropic/claude-sonnet-4-6",
    "production": "anthropic/claude-sonnet-4-6",
}

LLM_MODEL = os.getenv("LLM_MODEL", MODEL_CONFIG.get(ENV, MODEL_CONFIG["development"]))

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
