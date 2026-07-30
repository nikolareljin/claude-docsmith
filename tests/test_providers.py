from __future__ import annotations

import json

import httpx
import pytest

from claude_docsmith.cli import _resolve_model
from claude_docsmith.providers import (
    ProviderError,
    _generate_claude,
    _generate_ollama,
    discover_model,
)

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


def test_generate_claude_raises_after_retry_budget_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def mock_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(529, text="overloaded")

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setattr("claude_docsmith.providers._RETRY_DELAY", 0)
    with pytest.raises(ProviderError, match="after retries"):
        _generate_claude("claude-haiku-4-5-20251001", "prompt", timeout=5)


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


# ── Model discovery ──────────────────────────────────────────────────────────


def _clear_model_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DOCSMITH_MODEL", "DOCSMITH_CLAUDE_MODEL", "DOCSMITH_OLLAMA_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_no_model_identifier_is_hardcoded() -> None:
    """A pinned default goes stale on every release and may not exist locally."""
    import re
    from pathlib import Path

    pattern = re.compile(r"claude-(opus|sonnet|haiku|fable|mythos)-|llama\d|qwen\d|mistral")
    src = Path(__file__).resolve().parents[1] / "src" / "claude_docsmith"
    offenders = [
        path.name
        for path in src.glob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_discover_ollama_picks_most_recently_modified(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(url: str, **kwargs: object) -> httpx.Response:
        assert url.endswith("/api/tags")
        return httpx.Response(
            200,
            json={
                "models": [
                    {"name": "alpha:latest", "modified_at": "2026-01-01T00:00:00Z"},
                    {"name": "gamma:7b", "modified_at": "2026-06-01T00:00:00Z"},
                    {"name": "beta:3b", "modified_at": "2026-03-01T00:00:00Z"},
                ]
            },
        )

    monkeypatch.setattr(httpx, "get", mock_get)
    assert discover_model("ollama", timeout=5) == "gamma:7b"


def test_discover_ollama_errors_when_nothing_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda url, **kw: httpx.Response(200, json={"models": []}))
    with pytest.raises(ProviderError, match="No models are installed"):
        discover_model("ollama", timeout=5)


def test_discover_ollama_errors_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(url: str, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "get", boom)
    with pytest.raises(ProviderError, match="Could not reach Ollama"):
        discover_model("ollama", timeout=5)


def test_discover_ollama_honours_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.internal:11434")
    seen: list[str] = []

    def mock_get(url: str, **kwargs: object) -> httpx.Response:
        seen.append(url)
        return httpx.Response(200, json={"models": [{"name": "x:1", "modified_at": "2026-01-01"}]})

    monkeypatch.setattr(httpx, "get", mock_get)
    discover_model("ollama", timeout=5)
    assert seen == ["http://ollama.internal:11434/api/tags"]


def test_discover_claude_picks_newest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def mock_get(url: str, **kwargs: object) -> httpx.Response:
        assert url.endswith("/v1/models")
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "older-model", "created_at": "2025-01-01T00:00:00Z"},
                    {"id": "newest-model", "created_at": "2026-07-01T00:00:00Z"},
                    {"id": "middle-model", "created_at": "2026-01-01T00:00:00Z"},
                ]
            },
        )

    monkeypatch.setattr(httpx, "get", mock_get)
    assert discover_model("claude", timeout=5) == "newest-model"


def test_discover_claude_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY not set"):
        discover_model("claude", timeout=5)


def test_discover_claude_surfaces_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "get", lambda url, **kw: httpx.Response(403, text="Forbidden"))
    with pytest.raises(ProviderError, match="HTTP 403"):
        discover_model("claude", timeout=5)


def test_discover_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderError, match="Unsupported provider"):
        discover_model("gemini", timeout=5)


# ── Model resolution precedence ──────────────────────────────────────────────


def test_explicit_model_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCSMITH_CLAUDE_MODEL", "from-env")
    assert _resolve_model("claude", "from-flag") == "from-flag"


def test_provider_env_beats_generic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_model_env(monkeypatch)
    monkeypatch.setenv("DOCSMITH_MODEL", "generic")
    monkeypatch.setenv("DOCSMITH_OLLAMA_MODEL", "specific")
    assert _resolve_model("ollama", None) == "specific"


def test_generic_env_used_when_no_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_model_env(monkeypatch)
    monkeypatch.setenv("DOCSMITH_MODEL", "generic")
    assert _resolve_model("claude", None) == "generic"


def test_blank_env_falls_through_to_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_model_env(monkeypatch)
    monkeypatch.setenv("DOCSMITH_OLLAMA_MODEL", "   ")
    monkeypatch.setattr(
        httpx, "get", lambda url, **kw: httpx.Response(200, json={"models": [{"name": "found:1"}]})
    )
    assert _resolve_model("ollama", None) == "found:1"


def test_discovery_is_last_resort(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_model_env(monkeypatch)
    monkeypatch.setattr(
        httpx, "get", lambda url, **kw: httpx.Response(200, json={"models": [{"name": "found:1"}]})
    )
    assert _resolve_model("ollama", None) == "found:1"
