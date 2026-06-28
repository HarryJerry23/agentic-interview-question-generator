import re
import json
import time
from openai import OpenAI
from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL

_TRANSIENT_SIGNALS = ('429', '500', '502', '503', 'Connection', 'Timeout', 'timeout', 'rate limit')


def _call_with_retry(fn, max_retries: int = 3):
    """Retry fn() on transient API errors with exponential backoff (1s, 2s, 4s)."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            err = str(exc)
            is_transient = any(sig in err for sig in _TRANSIENT_SIGNALS)
            if not is_transient or attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    return _client


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response text, handling markdown code blocks."""
    if not text:
        return {}
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    on_usage=None,
) -> str:
    """Simple chat completion. Returns the text response."""
    client = get_client()
    response = _call_with_retry(lambda: client.chat.completions.create(
        model=model or LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    ))
    if on_usage and getattr(response, "usage", None):
        on_usage(response.usage)
    return response.choices[0].message.content or ""


def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    on_usage=None,
) -> dict:
    """Chat completion that returns parsed JSON. Handles models that don't support response_format."""
    client = get_client()

    msgs = [
        {"role": "system", "content": system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation, just JSON."},
        {"role": "user", "content": user_prompt},
    ]

    # Try with response_format first (some models require it)
    try:
        response = _call_with_retry(lambda: client.chat.completions.create(
            model=model or LLM_MODEL,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        ))
        if on_usage and getattr(response, "usage", None):
            on_usage(response.usage)
        text = response.choices[0].message.content or ""
        return _extract_json(text)
    except Exception:
        pass

    # Fallback: no response_format, parse JSON from text
    response = _call_with_retry(lambda: client.chat.completions.create(
        model=model or LLM_MODEL,
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
    ))
    if on_usage and getattr(response, "usage", None):
        on_usage(response.usage)
    text = response.choices[0].message.content or ""
    return _extract_json(text)
