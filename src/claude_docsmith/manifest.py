"""Machine-readable index of generated documentation plus a drift check.

The manifest records which pages were generated, for which track, and from which
source files (by content hash). That makes two things possible without a model
call: telling whether documentation still matches the code, and letting exporters
walk the documentation set in a defined order.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from . import audiences
from .models import GenerationResult, RepoSnapshot

SCHEMA_VERSION = 1
MANIFEST_SUBPATH = ".docsmith/manifest.json"


@dataclass(slots=True)
class DocEntry:
    path: str
    title: str
    audience: str
    action: str
    sha256: str


@dataclass(slots=True)
class SourceEntry:
    path: str
    sha256: str


@dataclass(slots=True)
class ScanSettings:
    max_files: int
    max_bytes_per_file: int
    max_context_kb: int
    skip_tests: bool
    redact_secrets: bool = True


@dataclass(slots=True)
class Manifest:
    schema_version: int
    tool_version: str
    generated_at: str
    detected_language: str
    docs_dir: str
    scan: ScanSettings
    tracks: dict[str, dict] = field(default_factory=dict)
    sources: list[SourceEntry] = field(default_factory=list)
    redactions: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class DriftReport:
    changed_sources: list[str] = field(default_factory=list)
    removed_sources: list[str] = field(default_factory=list)
    added_sources: list[str] = field(default_factory=list)
    missing_docs: list[str] = field(default_factory=list)
    modified_docs: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        """Locally modified docs are reported but never fail the check."""
        return bool(
            self.changed_sources or self.removed_sources or self.added_sources or self.missing_docs
        )

    def render(self) -> str:
        lines: list[str] = []
        for label, items in (
            ("changed since docs were generated", self.changed_sources),
            ("removed since docs were generated", self.removed_sources),
            ("added since docs were generated", self.added_sources),
            ("documented but now missing", self.missing_docs),
        ):
            for item in items:
                lines.append(f"- {item} ({label})")
        for item in self.modified_docs:
            lines.append(f"- {item} (locally edited, not counted as drift)")
        return "\n".join(lines)


def manifest_path(root: Path, docs_dir: str) -> Path:
    return root / docs_dir / MANIFEST_SUBPATH


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_generated_path(rel_path: str, docs_dir: str) -> bool:
    """True for paths this tool writes: the two track roots and the manifest."""
    root = PurePosixPath(docs_dir)
    prefixes = [f"{root.joinpath('.docsmith').as_posix()}/"]
    prefixes += [f"{audiences.track_root(audience, docs_dir)}/" for audience in audiences.ALL]
    normalized = PurePosixPath(rel_path).as_posix()
    return any(normalized.startswith(prefix) for prefix in prefixes)


def source_hashes(snapshot: RepoSnapshot, docs_dir: str) -> dict[str, str]:
    """Hash the scanned inputs, excluding this tool's own output.

    Generated documentation is re-scanned on the next run because it lives under
    ``docs/``. Counting it as a source would make every run report drift against
    the files it just wrote.
    """
    return {
        item.path: hash_text(item.content)
        for item in sorted(snapshot.scanned_files, key=lambda item: item.path)
        if not is_generated_path(item.path, docs_dir)
    }


def build(
    *,
    snapshot: RepoSnapshot,
    result: GenerationResult,
    tool_version: str,
    docs_dir: str,
    scan: ScanSettings,
    generated_at: str | None = None,
) -> Manifest:
    tracks: dict[str, dict] = {}
    for audience in audiences.ALL:
        entries = [
            DocEntry(
                path=item.path,
                title=_title_of(item.content, item.path),
                audience=audience.key,
                action=item.action,
                sha256=hash_text(item.content.rstrip() + "\n"),
            )
            for item in result.files
            if item.audience == audience.key
        ]
        tracks[audience.key] = {
            "root": audiences.track_root(audience, docs_dir),
            "files": [asdict(entry) for entry in sorted(entries, key=lambda e: e.path)],
        }

    sources = [
        SourceEntry(path=path, sha256=sha)
        for path, sha in source_hashes(snapshot, docs_dir).items()
    ]

    return Manifest(
        schema_version=SCHEMA_VERSION,
        tool_version=tool_version,
        generated_at=generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        detected_language=snapshot.detected_language,
        docs_dir=docs_dir,
        scan=scan,
        tracks=tracks,
        sources=sorted(sources, key=lambda entry: entry.path),
        redactions=snapshot.redaction_summary,
    )


def write(root: Path, manifest: Manifest) -> Path:
    destination = manifest_path(root, manifest.docs_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(asdict(manifest), indent=2) + "\n", encoding="utf-8")
    return destination


def read(root: Path, docs_dir: str) -> Manifest | None:
    path = manifest_path(root, docs_dir)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("schema_version") != SCHEMA_VERSION:
        return None
    scan_payload = payload.get("scan", {})
    return Manifest(
        schema_version=payload["schema_version"],
        tool_version=payload.get("tool_version", ""),
        generated_at=payload.get("generated_at", ""),
        detected_language=payload.get("detected_language", "unknown"),
        docs_dir=payload.get("docs_dir", docs_dir),
        scan=ScanSettings(
            max_files=scan_payload.get("max_files", 40),
            max_bytes_per_file=scan_payload.get("max_bytes_per_file", 8000),
            max_context_kb=scan_payload.get("max_context_kb", 128),
            skip_tests=scan_payload.get("skip_tests", False),
            redact_secrets=scan_payload.get("redact_secrets", True),
        ),
        tracks=payload.get("tracks", {}),
        sources=[
            SourceEntry(path=item["path"], sha256=item["sha256"])
            for item in payload.get("sources", [])
        ],
        redactions=payload.get("redactions", []),
    )


def check_drift(root: Path, manifest: Manifest, current_sources: dict[str, str]) -> DriftReport:
    """Compare recorded source hashes against ``current_sources`` (path -> sha256)."""
    report = DriftReport()
    recorded = {entry.path: entry.sha256 for entry in manifest.sources}

    for path, sha in recorded.items():
        current = current_sources.get(path)
        if current is None:
            report.removed_sources.append(path)
        elif current != sha:
            report.changed_sources.append(path)

    for path in current_sources:
        if path not in recorded:
            report.added_sources.append(path)

    for track in manifest.tracks.values():
        for entry in track.get("files", []):
            doc_path = root / entry["path"]
            if not doc_path.is_file():
                report.missing_docs.append(entry["path"])
            elif hash_file(doc_path) != entry["sha256"]:
                report.modified_docs.append(entry["path"])

    for items in (
        report.changed_sources,
        report.removed_sources,
        report.added_sources,
        report.missing_docs,
        report.modified_docs,
    ):
        items.sort()
    return report


def _title_of(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return Path(fallback).stem.replace("-", " ").replace("_", " ").title()
