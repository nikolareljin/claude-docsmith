from __future__ import annotations

from typing import Protocol

from .audiences import Audience, track_root
from .models import RepoSnapshot
from .redaction import MARKER_TEMPLATE


class SkillRoot(Protocol):
    def joinpath(self, *pathsegments: str) -> "SkillRoot": ...
    def read_text(self, encoding: str = "utf-8") -> str: ...


def build_prompt(
    snapshot: RepoSnapshot,
    skill_root: SkillRoot,
    audience: Audience,
    *,
    docs_dir: str = "docs",
    skip_checklists: bool = False,
) -> str:
    """Assemble the prompt for a single documentation track.

    Each track gets its own prompt and its own provider call, so the two
    audiences do not share one output token budget.
    """
    skill_text = _read(skill_root, "SKILL.md")
    reference_text = _read(skill_root, audience.reference)
    output_root = track_root(audience, docs_dir)

    sections = [
        f"You are generating the {audience.title} track of this repository's documentation.",
        "Return JSON only. Do not wrap in code fences.",
        _json_contract(audience, output_root),
        audience.contract_hint,
        f"Detected language: {snapshot.detected_language}",
        "Skill instructions:",
        skill_text,
        f"{audience.title} reference:",
        reference_text,
    ]

    if not skip_checklists:
        sections += [
            f"{audience.title} checklist:",
            _read(skill_root, audience.checklist),
        ]

    if snapshot.redactions or snapshot.skipped_sensitive:
        sections.append(_redaction_notice(snapshot))

    sections += [
        "Repository inventory:",
        "\n".join(f"- {line}" for line in snapshot.inventory),
        "Repository file excerpts:",
        _render_files(snapshot),
    ]

    return "\n\n".join(sections)


def _read(skill_root: SkillRoot, relative: str) -> str:
    node = skill_root
    for segment in relative.split("/"):
        node = node.joinpath(segment)
    return node.read_text(encoding="utf-8")


def _json_contract(audience: Audience, output_root: str) -> str:
    allowed = ", ".join((f"{output_root}/**", *audience.extra_allowed_paths))
    return (
        'Output schema: {"summary":"...","files":[{"path":"...","audience":"'
        + audience.key
        + '","action":"update|create","content":"..."}],'
        '"open_questions":["..."],"follow_up_docs":["..."]}. '
        f'Every "audience" value must be "{audience.key}". '
        f"Every \"path\" must be one of: {allowed}. Files written anywhere else are rejected. "
        "Prefer updating an existing page over creating a near-duplicate one."
    )


def _redaction_notice(snapshot: RepoSnapshot) -> str:
    lines = [
        "Security notice:",
        f"Credential-shaped values were replaced with {MARKER_TEMPLATE.format(kind='kind')} "
        "markers before this prompt was built.",
        "Never reproduce a marker in the documentation and never guess what it replaced. "
        "Describe the setting by name and say how a reader supplies their own value.",
    ]
    if snapshot.skipped_sensitive:
        listed = ", ".join(snapshot.skipped_sensitive[:10])
        lines.append(f"These files were deliberately not read: {listed}.")
    return "\n".join(lines)


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
