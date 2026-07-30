from __future__ import annotations

import os
import time

import httpx


class ProviderError(RuntimeError):
    pass


_RETRY_STATUSES = {429, 503, 529}
_RETRY_DELAY = 10
_MAX_RETRIES = 2


_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
_ANTHROPIC_VERSION = "2023-06-01"
_DISCOVERY_TIMEOUT = 30


def _ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def discover_model(provider: str, timeout: int = _DISCOVERY_TIMEOUT) -> str:
    """Ask the provider which model to use.

    No model identifier is hardcoded anywhere in this package: pinning one means
    it goes stale on the next release, and for Ollama it assumes a model the user
    may never have pulled. Callers should treat this as the last step of a
    precedence chain behind an explicit flag and an environment variable.
    """
    if provider == "ollama":
        return _discover_ollama(timeout)
    if provider == "claude":
        return _discover_claude(timeout)
    raise ProviderError(f"Unsupported provider: {provider}")


def _discover_ollama(timeout: int) -> str:
    """Most recently modified installed model, tie-broken by name for determinism."""
    base_url = _ollama_base_url()
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
    except Exception as exc:
        raise ProviderError(
            f"Could not reach Ollama at {base_url} to determine a model: {exc}. "
            "Pass --model or set DOCSMITH_OLLAMA_MODEL."
        ) from exc
    if response.status_code != 200:
        raise ProviderError(
            f"Ollama returned HTTP {response.status_code} when listing models. "
            "Pass --model or set DOCSMITH_OLLAMA_MODEL."
        )
    try:
        models = response.json().get("models", [])
    except Exception as exc:
        raise ProviderError("Ollama returned a non-JSON model list.") from exc

    names = [item.get("name") for item in models if isinstance(item, dict) and item.get("name")]
    if not names:
        raise ProviderError(
            f"No models are installed on the Ollama server at {base_url}. "
            "Pull one with `ollama pull <model>`, pass --model, or set DOCSMITH_OLLAMA_MODEL."
        )
    ranked = sorted(
        (item for item in models if isinstance(item, dict) and item.get("name")),
        key=lambda item: (str(item.get("modified_at", "")), str(item["name"])),
        reverse=True,
    )
    return str(ranked[0]["name"])


def _discover_claude(timeout: int) -> str:
    """Newest model the API key can see, by ``created_at``."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ProviderError("ANTHROPIC_API_KEY not set.")
    headers = {"x-api-key": api_key, "anthropic-version": _ANTHROPIC_VERSION}
    try:
        response = httpx.get(f"{_ANTHROPIC_BASE_URL}/v1/models", headers=headers, timeout=timeout)
    except Exception as exc:
        raise ProviderError(
            f"Could not reach the Claude API to determine a model: {exc}. "
            "Pass --model or set DOCSMITH_CLAUDE_MODEL."
        ) from exc
    if response.status_code != 200:
        raise ProviderError(
            f"Claude API returned HTTP {response.status_code} when listing models: "
            f"{response.text[:200]}"
        )
    try:
        data = response.json().get("data", [])
    except Exception as exc:
        raise ProviderError("Claude API returned a non-JSON model list.") from exc

    entries = [item for item in data if isinstance(item, dict) and item.get("id")]
    if not entries:
        raise ProviderError(
            "The Claude API returned no models for this key. "
            "Pass --model or set DOCSMITH_CLAUDE_MODEL."
        )
    ranked = sorted(
        entries,
        key=lambda item: (str(item.get("created_at", "")), str(item["id"])),
        reverse=True,
    )
    return str(ranked[0]["id"])


def generate_text(provider: str, model: str, prompt: str, timeout: int = 180) -> str:
    if provider == "ollama":
        return _generate_ollama(model, prompt, timeout)
    if provider == "claude":
        return _generate_claude(model, prompt, timeout)
    raise ProviderError(f"Unsupported provider: {provider}")


def _generate_ollama(model: str, prompt: str, timeout: int) -> str:
    base_url = _ollama_base_url()
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
        if response.status_code in _RETRY_STATUSES:
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
                continue
            break
        if response.status_code != 200:
            raise ProviderError(f"Ollama returned HTTP {response.status_code}: {response.text[:200]}")
        try:
            body = response.json()
        except Exception as exc:
            raise ProviderError(f"Ollama returned non-JSON response: {response.text[:200]}") from exc
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
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": _ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = httpx.post(
                f"{_ANTHROPIC_BASE_URL}/v1/messages",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
        except Exception as exc:
            raise ProviderError(f"Claude API request failed: {exc}") from exc
        if response.status_code in _RETRY_STATUSES:
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
                continue
            break
        if response.status_code != 200:
            raise ProviderError(f"Claude API returned HTTP {response.status_code}: {response.text[:200]}")
        try:
            body = response.json()
        except Exception as exc:
            raise ProviderError(f"Claude API returned non-JSON response: {response.text[:200]}") from exc
        content_blocks = body.get("content", [])
        if not isinstance(content_blocks, list):
            raise ProviderError("Claude API returned malformed content blocks.")
        text_parts: list[str] = []
        for block in content_blocks:
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            text = block.get("text")
            if isinstance(text, str):
                text_parts.append(text)
        if not text_parts and not any(
            isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
            for block in content_blocks
        ):
            raise ProviderError("Claude API returned no text content blocks.")
        text = "".join(text_parts).strip()
        if not text:
            raise ProviderError("Claude API returned an empty response.")
        return text
    raise ProviderError("Claude API request failed after retries.")
