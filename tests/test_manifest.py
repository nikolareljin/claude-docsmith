from pathlib import Path

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
