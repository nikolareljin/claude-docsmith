from __future__ import annotations

from pathlib import Path

from .models import RepoSnapshot


def build_prompt(snapshot: RepoSnapshot, skill_root: Path, skip_checklists: bool = False) -> str:
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    sections = [
        "You are generating repository documentation updates.",
        "Return JSON only. Do not wrap in code fences.",
        _json_contract(),
        f"Detected language: {snapshot.detected_language}",
        "Skill instructions:",
        skill_text,
    ]

    if not skip_checklists:
        user_checklist = (skill_root / "templates/user-doc-checklist.md").read_text(encoding="utf-8")
        developer_checklist = (skill_root / "templates/developer-doc-checklist.md").read_text(encoding="utf-8")
        sections += [
            "User documentation checklist:",
            user_checklist,
            "Developer documentation checklist:",
            developer_checklist,
        ]

    sections += [
        "Repository inventory:",
        "\n".join(f"- {line}" for line in snapshot.inventory),
        "Repository file excerpts:",
        _render_files(snapshot),
    ]

    return "\n\n".join(sections)


def _json_contract() -> str:
    return (
        'Output schema: {"summary":"...","files":[{"path":"...","audience":"user|developer",'
        '"action":"update|create","content":"..."}],"open_questions":["..."],"follow_up_docs":["..."]}. '
        "Prefer updating existing documentation files over creating new ones."
    )


def _render_files(snapshot: RepoSnapshot) -> str:
    rendered: list[str] = []
    for item in snapshot.scanned_files:
        rendered.append(
            "\n".join([
                f"FILE: {item.path}",
                f"CATEGORY: {item.category}",
                item.content,
            ])
        )
    return "\n\n".join(rendered)
