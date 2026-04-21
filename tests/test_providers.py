from __future__ import annotations

import json

import httpx
import pytest

from claude_docsmith.providers import ProviderError, _generate_claude, _generate_ollama


# ── Claude provider ──────────────────────────────────────────────────────────


def test_generate_claude_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY not set"):
        _generate_claude("claude-haiku-4-5-20251001", "hi", timeout=5)


def test_generate_claude_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    payload = json.dumps({"summary": "ok", "files": []})

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"content": [{"type": "text", "text": payload}]})

    monkeypatch.setattr(httpx, "post", mock_post)
    result = _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)
    assert result == payload


def test_generate_claude_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    monkeypatch.setattr(httpx, "post", mock_post)
    with pytest.raises(ProviderError, match="HTTP 401"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)


def test_generate_claude_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"content": [{"type": "text", "text": ""}]})

    monkeypatch.setattr(httpx, "post", mock_post)
    with pytest.raises(ProviderError, match="empty response"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)


def test_generate_claude_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    monkeypatch.setattr(httpx, "post", mock_post)
    with pytest.raises(ProviderError, match="no text content blocks"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)


def test_generate_claude_text_block_without_text_field(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    response = httpx.Response(200, json={"content": [{"type": "text"}]})
    monkeypatch.setattr("claude_docsmith.providers.httpx.post", lambda *args, **kwargs: response)

    with pytest.raises(ProviderError, match="no text content blocks"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)


def test_generate_claude_non_list_content_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    response = httpx.Response(200, json={"content": {"type": "text", "text": "hello"}})
    monkeypatch.setattr("claude_docsmith.providers.httpx.post", lambda *args, **kwargs: response)

    with pytest.raises(ProviderError, match="malformed content blocks"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)


def test_generate_claude_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    call_count = 0

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, text="rate limited")
        return httpx.Response(200, json={"content": [{"type": "text", "text": "ok"}]})

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setattr("claude_docsmith.providers._RETRY_DELAY", 0)
    result = _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)
    assert result == "ok"
    assert call_count == 2


# ── Ollama provider ──────────────────────────────────────────────────────────


def test_generate_ollama_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"response": "ollama result"})

    monkeypatch.setattr(httpx, "post", mock_post)
    result = _generate_ollama("llama3.1", "prompt", timeout=5)
    assert result == "ollama result"


def test_generate_ollama_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setattr("claude_docsmith.providers._RETRY_DELAY", 0)
    with pytest.raises(ProviderError, match="after retries"):
        _generate_ollama("llama3.1", "prompt", timeout=5)


def test_generate_claude_raises_after_retry_budget_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(529, text="overloaded")

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setattr("claude_docsmith.providers._RETRY_DELAY", 0)
    with pytest.raises(ProviderError, match="after retries"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)
