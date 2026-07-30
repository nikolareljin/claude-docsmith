"""Definitions of the two documentation tracks.

Every audience-specific decision lives here: which skill reference and checklist
a track loads, where its pages are written, and what page set the model is asked
for. Nothing else in the package branches on a bare ``"user"`` / ``"developer"``
string.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class Audience:
    key: str
    title: str
    output_root: str
    reference: str
    checklist: str
    extra_allowed_paths: tuple[str, ...]
    contract_hint: str


USER = Audience(
    key="user",
    title="User manual",
    output_root="user",
    reference="references/user-manual.md",
    checklist="templates/user-doc-checklist.md",
    extra_allowed_paths=("README.md",),
    contract_hint=(
        "Write the complete end-user manual. Required pages, all relative to the "
        "output root:\n"
        "- index.md: what the product does, who it is for, and an at-a-glance list of "
        "everything it can do, each item linking to its feature page.\n"
        "- getting-started.md: prerequisites, installation, first run, and the first "
        "task the reader completes successfully.\n"
        "- features/<slug>.md: one page per user-visible feature, screen, or command. "
        "Each page states what the feature is for, gives numbered steps, and documents "
        "every option or setting with what it does, its default, and when to change it.\n"
        "- troubleshooting.md: symptom, cause, fix, one section per failure a user can hit.\n"
        "- faq.md: real questions a non-technical reader asks.\n"
        "Reference screenshots as ![description](screenshots/<id>.png) using a stable "
        "kebab-case id. Write for a reader who will not open the source code: no "
        "internal type names, no module paths, no code blocks unless the reader types "
        "that text themselves."
    ),
)

DEVELOPER = Audience(
    key="developer",
    title="Developer reference",
    output_root="developer",
    reference="references/developer-reference.md",
    checklist="templates/developer-doc-checklist.md",
    extra_allowed_paths=(),
    contract_hint=(
        "Write the complete developer reference. Required pages, all relative to the "
        "output root:\n"
        "- index.md: how the codebase is organised and where to start reading.\n"
        "- architecture.md: components, responsibilities, data flow, boundaries.\n"
        "- api/index.md: every API surface the project exposes, grouped by version.\n"
        "- api/<version>/<resource>.md: one page per resource per API version when "
        "versioned endpoints exist (v1, v2, ...). Each endpoint documents method, path, "
        "auth, path/query/body parameters with types and required flags, response shape, "
        "status codes, and a worked request/response example.\n"
        "- reference/modules.md and reference/classes.md: public functions and classes "
        "with full signatures, parameter types, defaults, return types, raised errors, "
        "and base classes.\n"
        "- extending.md: extension points, which classes are meant to be subclassed, "
        "which interfaces to implement, and a worked example of doing so.\n"
        "Document only what exists in the code. Do not invent endpoints, parameters, or "
        "versions. When a version group has no endpoints, omit the page rather than "
        "writing a placeholder."
    ),
)

ALL: tuple[Audience, ...] = (USER, DEVELOPER)

CHOICES: tuple[str, ...] = tuple(audience.key for audience in ALL) + ("both",)


def resolve(name: str) -> tuple[Audience, ...]:
    """Map a ``--audience`` value to the tracks it selects."""
    if name == "both":
        return ALL
    for audience in ALL:
        if audience.key == name:
            return (audience,)
    raise ValueError(f"Unknown audience: {name}")


def by_key(key: str) -> Audience | None:
    for audience in ALL:
        if audience.key == key:
            return audience
    return None


def track_root(audience: Audience, docs_dir: str) -> str:
    """Repo-relative root for a track, e.g. ``docs/user``."""
    return PurePosixPath(docs_dir).joinpath(audience.output_root).as_posix()


def is_allowed_path(audience: Audience, rel_path: str, docs_dir: str) -> bool:
    """Return True when a generated file may be written to ``rel_path``.

    Files must live inside their own track's root. A small explicit allowlist
    covers shared entry points such as README.md for the user track.
    """
    candidate = PurePosixPath(rel_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    normalized = candidate.as_posix()
    if normalized in audience.extra_allowed_paths:
        return True
    root = track_root(audience, docs_dir)
    return normalized.startswith(f"{root}/")
