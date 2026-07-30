from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from . import audiences
from .redaction import Finding, summarize


@dataclass(slots=True)
class ScannedFile:
    path: str
    category: str
    content: str


@dataclass(slots=True)
class RepoSnapshot:
    root: Path
    scanned_files: list[ScannedFile]
    inventory: list[str]
    detected_language: str = "unknown"
    total_bytes: int = 0
    redactions: list[Finding] = field(default_factory=list)
    skipped_sensitive: list[str] = field(default_factory=list)

    @property
    def redaction_summary(self) -> list[dict[str, object]]:
        return summarize(self.redactions)


@dataclass(slots=True)
class GeneratedFile:
    path: str
    audience: str
    action: str
    content: str


@dataclass(slots=True)
class GenerationResult:
    summary: str
    files: list[GeneratedFile] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    follow_up_docs: list[str] = field(default_factory=list)

    @classmethod
    def from_json_text(cls, text: str, default_audience: str | None = None) -> "GenerationResult":
        candidate = text.strip()
        if candidate.startswith("```"):
            parts = candidate.split("```")
            candidate = ""
            for part in parts:
                stripped = part.strip()
                if stripped.startswith("json"):
                    candidate = stripped[4:].strip()
                    break
                if stripped.startswith("{"):
                    candidate = stripped
                    break
        payload = json.loads(candidate)
        files = [
            GeneratedFile(
                path=item["path"],
                audience=_normalize_audience(item.get("audience"), default_audience),
                action=item.get("action", "update"),
                content=item["content"],
            )
            for item in payload.get("files", [])
        ]
        return cls(
            summary=payload.get("summary", ""),
            files=files,
            open_questions=list(payload.get("open_questions", [])),
            follow_up_docs=list(payload.get("follow_up_docs", [])),
        )


def _normalize_audience(value: object, default_audience: str | None) -> str:
    """Trust the track we asked for over the label the model returned."""
    if default_audience is not None:
        return default_audience
    if isinstance(value, str) and audiences.by_key(value) is not None:
        return value
    return "unknown"
