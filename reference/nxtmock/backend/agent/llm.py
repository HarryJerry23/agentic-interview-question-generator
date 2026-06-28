"""The agent LLM — Claude Haiku 4.5 via OpenRouter's OpenAI-compatible chat endpoint.

One place to build the chat model. `get_llm()` returns a plain text model; `structured(Schema)`
returns a model that emits a validated pydantic object (used by split/plan/concept-check/feedback).
Generation + refine use the plain model (they emit MD `-END-` blocks parsed by `mcq_parser`).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_openai import ChatOpenAI

from backend.settings import settings

_PROMPTS = Path(__file__).resolve().parent / "prompts"


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.4) -> ChatOpenAI:
    """Chat model for generation. Slightly creative; deterministic enough to follow format."""
    return ChatOpenAI(
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=temperature,
        max_retries=2,      # absorb transient 429s when calls run concurrently (Feature 5.1)
        timeout=60,
    )


@lru_cache(maxsize=1)
def get_critic_llm() -> ChatOpenAI:
    """Low-temperature model for checking/planning/splitting — stable verdicts.

    Uses `settings.critic_model` (a STRONGER model than generation) so the rubric critic catches the
    subtle quality checkpoints a small model skips — giveaway option length (2.1/3.2), recall-only
    questions (5.1), weak distractors (2.5/5.3). Falls back to `openrouter_model` when unset."""
    return ChatOpenAI(
        model=settings.critic_model or settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0.0,
        max_retries=2,      # absorb transient 429s when calls run concurrently (Feature 5.1)
        timeout=60,
    )


def load_prompt(name: str) -> str:
    """Read a prompt template from backend/agent/prompts/ (e.g. '01_split_session')."""
    return (_PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def fill(template: str, **values: str) -> str:
    """Replace every {{placeholder}} with its value; raise if the TEMPLATE has any unbound.

    Validation runs against the template's OWN placeholders only — substituted values are data,
    not template, and must not be re-scanned. A session's content can legitimately contain
    `{{...}}` (e.g. prompt-engineering reading material with `{{CONCEPT}}`, `{{JOB_ROLE}}`); if we
    checked the rendered output we'd misread that injected text as unbound placeholders and crash.
    """
    import re
    declared = set(re.findall(r"\{\{(\w+)\}\}", template))
    missing = sorted(declared - set(values))
    if missing:
        raise ValueError(f"Unbound prompt placeholders: {missing}")
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", str(val))
    return out
