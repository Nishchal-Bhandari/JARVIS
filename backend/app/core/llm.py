"""Optional LLM path via OpenRouter (OpenAI-compatible chat completions).

No key -> returns None and callers fall back to the deterministic
template / intent-matching answers. Never raises: any failure (no key,
network error, bad response) degrades gracefully to the template.

Default model is a free OpenRouter model so limited credits are not
burned. Override with LLM_MODEL; other free models on OpenRouter include
e.g. "deepseek/deepseek-r1:free" and "qwen/qwen-2.5-7b-instruct:free"
(free-model availability changes, so check openrouter.ai/models).
Only the structured incident summary is ever sent — never raw logs.
"""

import os

import httpx

BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
TIMEOUT = 15.0


def complete(prompt: str, max_tokens: int = 400) -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "") or DEFAULT_MODEL
    if not key:
        return None
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "HTTP-Referer": os.environ.get("SITE_URL", "http://localhost:3000"),
                    "X-Title": "J.A.R.V.I.S.",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
