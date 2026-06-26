"""Typed settings, loaded from this folder's own .env (separate from any parent app).

Feature 1 only needs the memory-store DSN, the embedding endpoint, and chunking knobs.
Later features add their own keys to the same .env (placeholders are already present).
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# agentic-mcq-generation-workflow/.env  (this file lives at backend/settings.py)
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    # Memory store
    postgres_store_dsn: str

    # Embeddings (OpenAI-compatible endpoint)
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dims: int = 1536
    embedding_base_url: str = "https://openrouter.ai/api/v1"
    embedding_api_key: str = ""

    # Chunking (token-aware; tiktoken cl100k_base)
    chunk_target: int = 400
    chunk_max: int = 550
    chunk_overlap: int = 60

    # Agent LLM (OpenRouter, OpenAI-compatible chat endpoint) — Feature 3
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-haiku-4-5"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # The rubric critic uses a STRONGER model than generation: a small model reliably catches blatant
    # wrong-answers but is lenient on subtle quality checkpoints (giveaway option length 2.1/3.2,
    # recall-only 5.1, weak distractors 2.5/5.3), so flawed questions passed green. Blank → fall back
    # to `openrouter_model` (single-model deploys keep working).
    critic_model: str = "anthropic/claude-sonnet-4.5"

    # Operational DBs (Feature 3). Blank → fall back to the memory store DSN (one Neon DB;
    # LangGraph's checkpointer creates its own tables, our schema its own).
    agent_store_dsn: str = ""
    langgraph_checkpoint_dsn: str = ""

    # Where accepted classroom quizzes are written in the parent's structured format.
    # Blank → <repo_root>/generated_quizzes.
    generated_quizzes_dir: str = ""

    # Rubric phase (Feature 4). When a category's rejection-feedback rule reaches this many hits,
    # the referenced checkpoint is auto-refined in memory. Lower it (e.g. 1) to test promotion.
    rubric_promote_threshold: int = 3

    # Feedback retrieval (scalable, non-destructive memory). Controls HOW the learned authoring
    # rules are selected for prompt injection. "frequency" = today's behavior (top-k by hit_count,
    # zero embedding cost); "semantic" = vector-relevance to the current problem; "hybrid" = blend
    # of relevance + proven frequency (recommended once embeddings are backfilled). Ships
    # "frequency" so the feature is inert until you flip it in .env after backfilling.
    feedback_retrieval_mode: str = "frequency"  # "frequency" | "semantic" | "hybrid"
    feedback_semantic_k: int = 8                 # how many rules to inject
    feedback_candidate_limit: int = 200          # vector candidates pulled before re-ranking
    # Hybrid ranking weights (relevance + frequency + recency). Recency off by default — the rule
    # corpus is small, so recency adds noise until it grows.
    feedback_weight_semantic: float = 0.6
    feedback_weight_frequency: float = 0.4
    feedback_weight_recency: float = 0.0
    feedback_recency_half_life_days: int = 30
    # Cosine similarity above which two rules are treated as "the same lesson" — used to evolve
    # in place on write (bump hit_count + record the paraphrase) and to fold existing duplicates.
    # Tuned empirically for text-embedding-3-small: true paraphrases of one lesson cluster around
    # 0.82–0.88, while genuinely distinct rules score lower, so 0.85 catches duplicates without
    # merging distinct rules. Raise it to be more conservative; lower it to merge more aggressively.
    feedback_dedup_similarity: float = 0.85
    feedback_alias_cap: int = 10                 # max paraphrases stored per rule (bounded growth)

    # Latency + cost (Feature 5.1). Independent LLM calls run on a bounded thread pool; critic
    # scoring batches more questions per call (fewer calls + less redundant input).
    llm_max_concurrency: int = 6
    critic_batch_size: int = 8
    # OpenRouter list price for the agent model (USD per 1M tokens) — only for the report's $ estimate.
    price_input_per_m: float = 1.0      # claude-haiku-4-5 input
    price_output_per_m: float = 5.0     # claude-haiku-4-5 output
    # USD → INR conversion for displaying cost in Rupees (Feature 5.4). FALLBACK rate, used only when
    # the live FX fetch is unavailable/disabled. The live rate (cost.usd_to_inr_rate()) is preferred
    # so ₹ figures track the drifting rupee value automatically; override here via USD_TO_INR=...
    usd_to_inr: float = 83.5
    # Live USD→INR FX (follow-up to 5.4). fx_live=false pins the fixed usd_to_inr above. The endpoint
    # is free + keyless; the rate is cached fx_cache_ttl_seconds (default 6h — FX moves slowly).
    fx_live: bool = True
    fx_api_url: str = "https://open.er-api.com/v6/latest/USD"
    fx_cache_ttl_seconds: int = 21600

    # Observability (Feature 5.1). LangSmith auto-traces every LangChain LLM call when enabled.
    # Set these in .env; init_tracing() exports them to the env vars LangChain reads.
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "agentic-mcq-workflow"

    # ── Mock Interview (Feature 11) — harvest REAL interview questions from legitimate sources ──
    interview_src_github_enabled: bool = True
    github_token: str = ""               # optional → lifts the GitHub API rate limit (60→5000/hr)
    # Cosine threshold for embedding dedup + cross-source clustering. Calibrated on text-embedding-3-small:
    # identical→1.0, true paraphrases of one question→~0.85, distinct questions→≤0.7, unrelated→~0.2.
    # 0.84 merges reworded duplicates without collapsing distinct questions.
    interview_dedup_similarity: float = 0.84
    tavily_api_key: str = ""             # the Tavily search-extract connector (Part 2). Blank → disabled.
    # Part 2 connector toggles. Tavily is the breadth layer over interview_source_allowlist (covers
    # GeeksforGeeks / AmbitionBox / Glassdoor / Levels / Blind / … legitimately via search, no scraping).
    interview_src_tavily_enabled: bool = True       # effective only when tavily_api_key is set
    interview_src_reddit_enabled: bool = False      # needs a Reddit app credential (below)
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "nxtwave-mock-interview/1.0"
    # Evidence engine (Part 2). A question publishes only with > min_sources INDEPENDENT domains + a
    # named company + resolving links; under-bar candidates trigger up to research_rounds re-searches.
    interview_min_sources: int = 2
    interview_research_rounds: int = 3
    tavily_max_results: int = 6          # results per Tavily query
    # License-clean company-tagged GitHub repos (spec 10 §F.2 group C, URL-verified). "owner/repo".
    interview_github_repos: list[str] = [
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
        # Round 2 (+14, URL-verified) — spec 10 §F.2
        "chiphuyen/ml-interviews-book",
        "chiphuyen/machine-learning-systems-design",
        "alexeygrigorev/data-science-interviews",
        "zhengjingwei/machine-learning-interview",
        "iamtodor/data-science-interview-questions-and-answers",
        "theainerd/MLInterview",
        "Devinterview-io/data-scientist-interview-questions",
        "Devinterview-io/deep-learning-interview-questions",
        "Devinterview-io/pytorch-interview-questions",
        "Devinterview-io/nlp-interview-questions",
        "Devinterview-io/computer-vision-interview-questions",
        "Devinterview-io/tensorflow-interview-questions",
        "Devinterview-io/statistics-interview-questions",
    ]
    # Verified legitimate domains for the Part-2 Tavily search-extract layer (spec 10 §F.2 A1+A2+A3+B1).
    interview_source_allowlist: list[str] = [
        "tryexponent.com", "datalemur.com", "stratascratch.com", "prachub.com", "interviewquery.com",
        "prepfully.com", "igotanoffer.com", "glassdoor.com", "teamblind.com", "leetcode.com",
        "indeed.com", "interviewing.io", "hellointerview.com", "ambitionbox.com", "geeksforgeeks.org",
        "interviewbit.com", "prepinsta.com", "indiabix.com", "naukri.com", "reddit.com", "medium.com",
        "quora.com", "datascience.stackexchange.com", "stats.stackexchange.com", "stackoverflow.com",
        "datacamp.com", "analyticsvidhya.com", "kdnuggets.com", "towardsai.net", "towardsdatascience.com",
        "tredence.com", "igmguru.com", "vinsys.com", "novelvista.com", "generativeaimasters.in",
        "blockchain-council.org", "amquesteducation.com", "simplilearn.com", "edureka.co",
        "intellipaat.com", "projectpro.io", "turing.com", "springboard.com", "mlstack.cafe",
        "365datascience.com", "builtin.com",
        # Round 2 (+24, URL-verified) — spec 10 §F.2
        "datainterview.com", "huyenchip.com", "deep-ml.com", "finalroundai.com", "hackr.io",
        "mindmajix.com", "knowledgehut.com", "analyticsinsight.net", "freecodecamp.org",
        "machinelearninginterviews.com", "appliedaicourse.com",
        "faceprep.in", "hirist.tech", "upgrad.com", "mygreatlearning.com", "guvi.in", "boardinfinity.com",
        "herovired.com", "almabetter.com", "futurense.com", "theknowledgeacademy.com", "foundit.in",
        "whizlabs.com",
    ]

    @property
    def agent_dsn(self) -> str:
        return self.agent_store_dsn or self.postgres_store_dsn

    @property
    def checkpoint_dsn(self) -> str:
        return self.langgraph_checkpoint_dsn or self.postgres_store_dsn

    @property
    def quizzes_dir(self) -> str:
        return self.generated_quizzes_dir or str(_ENV_FILE.parent / "generated_quizzes")


settings = Settings()  # import-time singleton; reads .env once
