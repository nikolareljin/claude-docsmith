from __future__ import annotations

import json
import os
from urllib import request


class ProviderError(RuntimeError):
    pass


def generate_text(provider: str, model: str, prompt: str, timeout: int = 180) -> str:
    if provider == "anthropic":
        return _generate_anthropic(model, prompt, timeout)
    if provider == "ollama":
        return _generate_ollama(model, prompt, timeout)
    raise ProviderError(f"Unsupported provider: {provider}")


def _generate_anthropic(model: str, prompt: str, timeout: int) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ProviderError("ANTHROPIC_API_KEY is required for the anthropic provider.")

    payload = {
        "model": model,
        "max_tokens": 4000,
        "system": "You update repository documentation and must return valid JSON only.",
        "messages": [{"role": "user", "content": prompt}],
    }
    req = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"Anthropic request failed: {exc}") from exc

    parts = body.get("content", [])
    text_parts = [part.get("text", "") for part in parts if part.get("type") == "text"]
    return "\n".join(text_parts).strip()


def _generate_ollama(model: str, prompt: str, timeout: int) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    req = request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"Ollama request failed: {exc}") from exc

    generated = body.get("response", "").strip()
    if not generated:
        raise ProviderError("Ollama returned an empty response.")
    return generated
