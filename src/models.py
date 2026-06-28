from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator
import uuid


def new_uuid() -> str:
    return str(uuid.uuid4())


# --- Generation Config (user input) ---

class GenerationConfig(BaseModel):
    session_names: list[str]          # One or more sessions to combine
    max_questions: int = 15
    min_questions: int = 5
    difficulty_bias: dict[str, float] = Field(
        default_factory=lambda: {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    )
    dry_run: bool = False

    @property
    def session_name(self) -> str:
        """Combined session name for display."""
        return " + ".join(self.session_names)


# --- Topic Resolution Models ---

class KPMatch(BaseModel):
    kp_id: str                    # "KP_GLOBAL_0777"
    kp_label: str                 # "Zero-shot prompting techniques"
    relevance: float              # 0.0 - 1.0
    source_file: str              # "gen_ai_final.json"


class TopicMatch(BaseModel):
    topic: str                    # "AI_ML"
    sub_topic: str | None = None  # "PROMPT_ENGINEERING"
    confidence: float             # 0.0 - 1.0


class SessionContext(BaseModel):
    session_name: str
    learning_outcomes: list[str]
    key_concepts: list[str]
    scope_in: list[str]
    scope_out: list[str]
    session_type: Literal["theory_heavy", "code_heavy", "mixed"]
    matched_kp_ids: list[KPMatch]
    matched_csv_topics: list[TopicMatch]
    prerequisite_kp_chain: list[str]  # ordered KP IDs
    difficulty_distribution: dict[str, float]


# --- Question Models (output rows) ---

class QuestionDetail(BaseModel):
    question_id: str = Field(default_factory=new_uuid)
    category: str                           # GEN_AI, LLM, PYTHON, SQL, DSA, RESUME_DEEP_DIVE
    content: str                            # Full question text
    topic: str
    sub_topic: str | None = None
    difficulty: str | None = None           # Easy / Medium / Hard
    language: str | None = None
    framework: str | None = None
    tool: str | None = None
    asked_in_company: str | None = None
    role: str | None = None
    source_url: str | None = None
    source: Literal["curriculum", "interview_db", "web", "generated"]
    kp_label: str | None = None
    expected_answer: str | None = None

    @field_validator("expected_answer", mode="before")
    @classmethod
    def coerce_answer(cls, v):
        if isinstance(v, list):
            return "\n".join(str(item) for item in v)
        return v


class CodingQuestion(BaseModel):
    id: str = Field(default_factory=new_uuid)
    category: str                           # SQL_CODING_DEEP_DIVE, PYTHON_CODING, LLM_APP_CODING
    title: str
    content: str                            # Markdown problem statement
    code_id: str | None = None              # Links to CodeSnippet
    topic: str
    sub_topic: str | None = None
    difficulty: str | None = None
    language: str
    framework: str | None = None
    tool: str | None = None
    asked_in_company: str | None = None
    source: Literal["curriculum", "interview_db", "web", "generated"]
    expected_answer: str | None = None


class CodeSnippet(BaseModel):
    code_id: str
    code_content: str
    language: str                           # PYTHON, CPP, JAVA, JAVASCRIPT, SQL


class CodeAnalysisQuestion(BaseModel):
    """Code analysis / MCQ question — from Excel Sheet 8 format.

    The student reads a code snippet (linked via code_id) and answers the question.
    """
    question_id: str = Field(default_factory=new_uuid)
    tag_name: str                            # e.g. "python_code_analysis"
    content: str                             # Problem description / question text
    code_id: str                             # Links to CodeSnippet with the code to analyze
    title: str                               # Short title e.g. "Validate_subsequence"
    correct_answer: str | None = None        # Expected output / correct option
    difficulty: str | None = None
    topic: str | None = None
    source: Literal["curriculum", "interview_db", "web", "generated"] = "curriculum"


# --- Pipeline Output Models ---

class LocalPool(BaseModel):
    curriculum_questions: list[QuestionDetail] = Field(default_factory=list)
    interview_questions: list[QuestionDetail] = Field(default_factory=list)
    coding_questions: list[CodingQuestion] = Field(default_factory=list)
    code_snippets: list[CodeSnippet] = Field(default_factory=list)
    local_count: int = 0


class WebPool(BaseModel):
    web_questions: list[QuestionDetail] = Field(default_factory=list)
    web_coding_questions: list[CodingQuestion] = Field(default_factory=list)


class CurationMetadata(BaseModel):
    total_candidates: int = 0
    dedup_removed: int = 0
    source_counts: dict[str, int] = Field(default_factory=dict)
    questions_from_web: int = 0


class CuratedOutput(BaseModel):
    question_details: list[QuestionDetail] = Field(default_factory=list)
    coding_questions: list[CodingQuestion] = Field(default_factory=list)
    code_snippets: list[CodeSnippet] = Field(default_factory=list)
    metadata: CurationMetadata = Field(default_factory=CurationMetadata)


class FlaggedQuestion(BaseModel):
    question_id: str
    reason: str
    score: float


class QualityReport(BaseModel):
    composite_score: float = 0.0
    metric_scores: dict[str, float] = Field(default_factory=dict)
    pass_fail: Literal["pass", "fail"] = "fail"
    flagged_questions: list[FlaggedQuestion] = Field(default_factory=list)
    critique: list[str] = Field(default_factory=list)
    loops_used: int = 0
    api_usage: dict = Field(default_factory=dict)
