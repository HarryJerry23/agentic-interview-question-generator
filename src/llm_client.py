import re
import json
import time
from openai import OpenAI
from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL

# ── OpenRouter credit balance (cached) ────────────────────────────────────────
_credit_cache: dict = {"at": 0.0, "value": None}
_CREDIT_TTL = 60  # seconds


def get_credit_balance() -> dict | None:
    """Return OpenRouter balance for the current key, cached ~60s.

    Shape: {remaining, scope, account_remaining, key_limit, key_remaining}.
    `remaining` is the binding spendable balance — the per-key limit if the key
    is capped, else the account balance. Returns None on failure.
    """
    now = time.time()
    if _credit_cache["value"] is not None and now - _credit_cache["at"] < _CREDIT_TTL:
        return _credit_cache["value"]
    if not OPENROUTER_API_KEY:
        return None

    import requests
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    result: dict = {}
    try:
        # Account-level balance
        c = requests.get(f"{OPENROUTER_BASE_URL}/credits", headers=headers, timeout=10)
        if c.ok:
            d = c.json().get("data", {})
            total = d.get("total_credits")
            used = d.get("total_usage")
            if total is not None and used is not None:
                result["account_remaining"] = round(total - used, 2)

        # Per-key limit (the binding cap, if any)
        k = requests.get(f"{OPENROUTER_BASE_URL}/auth/key", headers=headers, timeout=10)
        if k.ok:
            d = k.json().get("data", {})
            result["key_limit"] = d.get("limit")
            rem = d.get("limit_remaining")
            if rem is not None:
                result["key_remaining"] = round(rem, 2)
    except Exception:
        return _credit_cache["value"]  # serve last good value if any

    if not result:
        return None

    if result.get("key_remaining") is not None:
        result["remaining"] = result["key_remaining"]
        result["scope"] = "key"
    elif result.get("account_remaining") is not None:
        result["remaining"] = result["account_remaining"]
        result["scope"] = "account"

    _credit_cache.update(at=now, value=result)
    return result

_TRANSIENT_SIGNALS = ('429', '500', '502', '503', 'Connection', 'Timeout', 'timeout', 'rate limit')

# Runtime-selectable model (set per generation from the UI). Falls back to the
# configured LLM_MODEL. Lets the user switch models without editing config/restarting.
_active_model: str | None = None


def set_active_model(model: str | None):
    global _active_model
    _active_model = model.strip() if model and model.strip() else None


def get_active_model() -> str:
    return _active_model or LLM_MODEL


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
        model=model or get_active_model(),
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
            model=model or get_active_model(),
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
        model=model or get_active_model(),
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
    ))
    if on_usage and getattr(response, "usage", None):
        on_usage(response.usage)
    text = response.choices[0].message.content or ""
    return _extract_json(text)
