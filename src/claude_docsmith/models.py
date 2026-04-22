from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


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
    def from_json_text(cls, text: str) -> "GenerationResult":
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
                audience=item.get("audience", "unknown"),
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
