from __future__ import annotations

import os
import time

import httpx


class ProviderError(RuntimeError):
    pass


_RETRY_STATUSES = {429, 503, 529}
_RETRY_DELAY = 10
_MAX_RETRIES = 2


def generate_text(provider: str, model: str, prompt: str, timeout: int = 180) -> str:
    if provider == "ollama":
        return _generate_ollama(model, prompt, timeout)
    if provider == "claude":
        return _generate_claude(model, prompt, timeout)
    raise ProviderError(f"Unsupported provider: {provider}")


def _generate_ollama(model: str, prompt: str, timeout: int) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    payload = {"model": model, "prompt": prompt, "stream": False, "format": "json"}
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = httpx.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
        except Exception as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc
        if response.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY)
            continue
        if response.status_code != 200:
            raise ProviderError(f"Ollama returned HTTP {response.status_code}: {response.text[:200]}")
        body = response.json()
        generated = body.get("response", "").strip()
        if not generated:
            raise ProviderError("Ollama returned an empty response.")
        return generated
    raise ProviderError("Ollama request failed after retries.")


def _generate_claude(model: str, prompt: str, timeout: int) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ProviderError("ANTHROPIC_API_KEY not set.")
    payload = {
        "model": model,
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
        except Exception as exc:
            raise ProviderError(f"Claude API request failed: {exc}") from exc
        if response.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY)
            continue
        if response.status_code != 200:
            raise ProviderError(f"Claude API returned HTTP {response.status_code}: {response.text[:200]}")
        body = response.json()
        try:
            text = body["content"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"Unexpected Claude API response shape: {exc}") from exc
        if not text:
            raise ProviderError("Claude API returned an empty response.")
        return text
    raise ProviderError("Claude API request failed after retries.")
