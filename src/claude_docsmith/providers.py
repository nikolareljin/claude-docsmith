from __future__ import annotations

import json
import os
from urllib import request


class ProviderError(RuntimeError):
    pass


def generate_text(provider: str, model: str, prompt: str, timeout: int = 180) -> str:
    if provider == "ollama":
        return _generate_ollama(model, prompt, timeout)
    raise ProviderError(f"Unsupported provider: {provider}")


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
