import json
from pathlib import Path

import pytest

from claude_docsmith import manifest as manifest_module
from claude_docsmith.models import GeneratedFile, GenerationResult, RepoSnapshot, ScannedFile
from claude_docsmith.redaction import Finding


def _scan() -> manifest_module.ScanSettings:
    return manifest_module.ScanSettings(
        max_files=40,
        max_bytes_per_file=8000,
        max_context_kb=128,
        skip_tests=False,
    )


def _snapshot(tmp_path: Path) -> RepoSnapshot:
    return RepoSnapshot(
        root=tmp_path,
        scanned_files=[
            ScannedFile(path="README.md", category="doc-or-config", content="# Test\n"),
            ScannedFile(path="src/app.py", category="source", content="x = 1\n"),
        ],
        inventory=["README.md", "src/app.py"],
        detected_language="python",
        total_bytes=14,
        redactions=[Finding(path="src/app.py", line=1, kind="anthropic-key")],
    )


def _result() -> GenerationResult:
    return GenerationResult(
        summary="",
        files=[
            GeneratedFile(path="docs/user/index.md", audience="user", action="create", content="# Guide\n"),
            GeneratedFile(
                path="docs/developer/index.md",
                audience="developer",
                action="create",
                content="# Reference\n",
            ),
        ],
    )


def _build(tmp_path: Path) -> manifest_module.Manifest:
    return manifest_module.build(
        snapshot=_snapshot(tmp_path),
        result=_result(),
        tool_version="1.1.0",
        docs_dir="docs",
        scan=_scan(),
        generated_at="2026-01-01T00:00:00Z",
    )


def _write_docs(tmp_path: Path) -> None:
    for item in _result().files:
        path = tmp_path / item.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.content.rstrip() + "\n", encoding="utf-8")


def test_manifest_round_trips(tmp_path: Path) -> None:
    written = manifest_module.write(tmp_path, _build(tmp_path))
    assert written == tmp_path / "docs" / ".docsmith" / "manifest.json"

    stored = manifest_module.read(tmp_path, "docs")
    assert stored is not None
    assert stored.schema_version == manifest_module.SCHEMA_VERSION
    assert stored.tool_version == "1.1.0"
    assert sorted(stored.tracks) == ["developer", "user"]
    assert stored.tracks["developer"]["files"][0]["title"] == "Reference"
    assert [entry.path for entry in stored.sources] == ["README.md", "src/app.py"]
    assert stored.redactions == [{"path": "src/app.py", "kind": "anthropic-key", "count": 1}]


def test_read_rejects_unknown_schema_version(tmp_path: Path) -> None:
    path = manifest_module.manifest_path(tmp_path, "docs")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"schema_version": 999}', encoding="utf-8")
    assert manifest_module.read(tmp_path, "docs") is None


def test_no_drift_when_sources_unchanged(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    stored = _build(tmp_path)
    current = {entry.path: entry.sha256 for entry in stored.sources}
    report = manifest_module.check_drift(tmp_path, stored, current)
    assert not report.has_drift


def test_changed_source_is_drift(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    stored = _build(tmp_path)
    current = {entry.path: entry.sha256 for entry in stored.sources}
    current["src/app.py"] = "0" * 64
    report = manifest_module.check_drift(tmp_path, stored, current)
    assert report.changed_sources == ["src/app.py"]
    assert report.has_drift


def test_added_and_removed_sources_are_drift(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    stored = _build(tmp_path)
    current = {entry.path: entry.sha256 for entry in stored.sources}
    current.pop("README.md")
    current["src/new.py"] = "1" * 64
    report = manifest_module.check_drift(tmp_path, stored, current)
    assert report.removed_sources == ["README.md"]
    assert report.added_sources == ["src/new.py"]


def test_missing_doc_is_drift_but_local_edit_is_not(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    stored = _build(tmp_path)
    current = {entry.path: entry.sha256 for entry in stored.sources}

    (tmp_path / "docs" / "user" / "index.md").write_text("# Guide\n\nHand edit.\n", encoding="utf-8")
    report = manifest_module.check_drift(tmp_path, stored, current)
    assert report.modified_docs == ["docs/user/index.md"]
    assert not report.has_drift

    (tmp_path / "docs" / "developer" / "index.md").unlink()
    report = manifest_module.check_drift(tmp_path, stored, current)
    assert report.missing_docs == ["docs/developer/index.md"]
    assert report.has_drift


def test_generated_docs_are_not_counted_as_sources(tmp_path: Path) -> None:
    snapshot = RepoSnapshot(
        root=tmp_path,
        scanned_files=[
            ScannedFile(path="README.md", category="doc-or-config", content="# Test\n"),
            ScannedFile(path="docs/user/index.md", category="doc-or-config", content="# Guide\n"),
            ScannedFile(path="docs/developer/api/index.md", category="doc-or-config", content="# API\n"),
            ScannedFile(path="docs/.docsmith/manifest.json", category="doc-or-config", content="{}"),
            ScannedFile(path="docs/adr/0001.md", category="doc-or-config", content="# ADR\n"),
        ],
        inventory=[],
    )
    assert sorted(manifest_module.source_hashes(snapshot, "docs")) == ["README.md", "docs/adr/0001.md"]


def test_generated_path_detection_respects_docs_dir() -> None:
    assert manifest_module.is_generated_path("documentation/user/index.md", "documentation")
    assert not manifest_module.is_generated_path("docs/user/index.md", "documentation")


# ── Untrusted manifest input ─────────────────────────────────────────────────
# docs/.docsmith/manifest.json lives in the repository being checked, so --check
# must treat it as attacker-controlled: it is meant to be safe to run in CI
# against code the operator does not control.


def _manifest_with_doc_entry(tmp_path: Path, entry: object) -> manifest_module.Manifest:
    stored = _build(tmp_path)
    stored.tracks = {"user": {"root": "docs/user", "files": [entry]}}
    return stored


@pytest.mark.parametrize(
    "hostile",
    [
        "/etc/passwd",
        "../../../etc/passwd",
        "docs/user/../../../etc/passwd",
        "",
        "   ",
    ],
)
def test_paths_escaping_the_repo_are_refused(tmp_path: Path, hostile: str) -> None:
    stored = _manifest_with_doc_entry(tmp_path, {"path": hostile, "sha256": "0" * 64})
    report = manifest_module.check_drift(tmp_path, stored, {})
    assert report.invalid_entries, hostile
    assert report.missing_docs == []
    assert report.modified_docs == []
    assert report.has_drift


def test_symlink_escape_is_refused(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    (tmp_path / "docs" / "user").mkdir(parents=True)
    link = tmp_path / "docs" / "user" / "index.md"
    link.symlink_to(outside)

    stored = _manifest_with_doc_entry(tmp_path, {"path": "docs/user/index.md", "sha256": "0" * 64})
    report = manifest_module.check_drift(tmp_path, stored, {})
    assert report.invalid_entries == ["docs/user/index.md"]
    assert report.modified_docs == []


@pytest.mark.parametrize(
    "entry",
    [
        {},
        {"path": "docs/user/index.md"},
        {"sha256": "0" * 64},
        {"path": 42, "sha256": "0" * 64},
        {"path": "docs/user/index.md", "sha256": 7},
        {"path": None, "sha256": None},
        "not-a-dict",
        None,
    ],
)
def test_malformed_doc_entries_are_drift_not_a_crash(tmp_path: Path, entry: object) -> None:
    stored = _manifest_with_doc_entry(tmp_path, entry)
    report = manifest_module.check_drift(tmp_path, stored, {})
    assert report.invalid_entries
    assert report.has_drift


@pytest.mark.parametrize("tracks", [{"user": "not-a-dict"}, {"user": {"files": "not-a-list"}}])
def test_malformed_track_structures_are_drift_not_a_crash(tmp_path: Path, tracks: dict) -> None:
    stored = _build(tmp_path)
    stored.tracks = tracks
    report = manifest_module.check_drift(tmp_path, stored, {})
    assert report.invalid_entries
    assert report.has_drift


@pytest.mark.parametrize(
    "payload",
    [
        '{"schema_version": 1}',
        '{"schema_version": 1, "sources": [{"path": "a.py"}]}',
        '{"schema_version": 1, "sources": "not-a-list", "tracks": [], "scan": 3}',
        '{"schema_version": 1, "redactions": "nope"}',
        '["not", "an", "object"]',
        '"just a string"',
    ],
)
def test_read_never_raises_on_a_malformed_manifest(tmp_path: Path, payload: str) -> None:
    path = manifest_module.manifest_path(tmp_path, "docs")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    stored = manifest_module.read(tmp_path, "docs")
    assert stored is None or isinstance(stored, manifest_module.Manifest)


def test_read_drops_malformed_source_entries_rather_than_crashing(tmp_path: Path) -> None:
    path = manifest_module.manifest_path(tmp_path, "docs")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"schema_version": 1, "sources": ['
        '{"path": "good.py", "sha256": "abc"},'
        '{"path": "missing-hash.py"},'
        '{"sha256": "orphan"},'
        '"not-a-dict"]}',
        encoding="utf-8",
    )
    stored = manifest_module.read(tmp_path, "docs")
    assert stored is not None
    assert [entry.path for entry in stored.sources] == ["good.py"]


def test_safe_repo_path_accepts_an_ordinary_relative_path(tmp_path: Path) -> None:
    (tmp_path / "docs" / "user").mkdir(parents=True)
    (tmp_path / "docs" / "user" / "index.md").write_text("x\n", encoding="utf-8")
    resolved = manifest_module.safe_repo_path(tmp_path, "docs/user/index.md")
    assert resolved == (tmp_path / "docs" / "user" / "index.md").resolve()


@pytest.mark.parametrize(
    "scan,expected",
    [
        ({"max_context_kb": 99_999_999}, ("max_context_kb", 10_240)),
        ({"max_files": 10 ** 9}, ("max_files", 5_000)),
        ({"max_bytes_per_file": 10 ** 9}, ("max_bytes_per_file", 1_000_000)),
        ({"max_files": 0}, ("max_files", 1)),
        ({"max_files": -5}, ("max_files", 1)),
        ({"max_files": "lots"}, ("max_files", 40)),
        ({"max_files": None}, ("max_files", 40)),
        ({"max_files": True}, ("max_files", 40)),
    ],
)
def test_scan_settings_from_a_manifest_are_clamped(tmp_path: Path, scan: dict, expected: tuple) -> None:
    """--check replays these into scan_repository, so an oversized value would
    turn a cheap offline check into reading the whole repository into memory."""
    path = manifest_module.manifest_path(tmp_path, "docs")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "scan": scan}), encoding="utf-8")

    stored = manifest_module.read(tmp_path, "docs")
    assert stored is not None
    field_name, value = expected
    assert getattr(stored.scan, field_name) == value


def test_non_string_metadata_falls_back_to_defaults(tmp_path: Path) -> None:
    path = manifest_module.manifest_path(tmp_path, "docs")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tool_version": {"nope": 1},
                "generated_at": 12345,
                "detected_language": ["python"],
                "docs_dir": None,
            }
        ),
        encoding="utf-8",
    )
    stored = manifest_module.read(tmp_path, "docs")
    assert stored is not None
    assert stored.tool_version == ""
    assert stored.generated_at == ""
    assert stored.detected_language == "unknown"
    assert stored.docs_dir == "docs"
