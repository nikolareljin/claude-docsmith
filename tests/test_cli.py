import argparse
from pathlib import Path

import pytest

from claude_docsmith import audiences, manifest as manifest_module
from claude_docsmith.cli import _apply_result, _resolve_skill_root, _run_check
from claude_docsmith.models import GeneratedFile, GenerationResult, RepoSnapshot, ScannedFile


def _args(**overrides) -> argparse.Namespace:
    defaults = dict(
        docs_dir="docs",
        redact=True,
        max_files=40,
        max_bytes_per_file=8000,
        max_context_kb=128,
        skip_tests=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _snapshot(tmp_path: Path) -> RepoSnapshot:
    return RepoSnapshot(
        root=tmp_path,
        scanned_files=[ScannedFile(path="README.md", category="doc-or-config", content="# Test\n")],
        inventory=["README.md"],
        detected_language="python",
        total_bytes=8,
    )


def _make_result(
    path: str = "docs/user/index.md",
    content: str = "# Hello\n",
    audience: str = "user",
) -> GenerationResult:
    return GenerationResult(
        summary="test summary",
        files=[GeneratedFile(path=path, audience=audience, action="create", content=content)],
    )


def test_apply_result_writes_file(tmp_path: Path) -> None:
    _apply_result(tmp_path, _make_result(), _args(), _snapshot(tmp_path))
    out = tmp_path / "docs" / "user" / "index.md"
    assert out.read_text(encoding="utf-8").startswith("# Hello")


def test_apply_result_adds_trailing_newline(tmp_path: Path) -> None:
    _apply_result(tmp_path, _make_result("README.md", "no newline"), _args(), _snapshot(tmp_path))
    assert (tmp_path / "README.md").read_text(encoding="utf-8").endswith("\n")


def test_apply_result_accepts_relative_target_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _apply_result(Path("."), _make_result(), _args(), _snapshot(tmp_path))
    assert (tmp_path / "docs" / "user" / "index.md").read_text(encoding="utf-8").startswith("# Hello")


def test_apply_result_rejects_path_traversal(tmp_path: Path) -> None:
    result = _make_result("../../etc/passwd", "evil")
    with pytest.raises(ValueError, match="Refusing to write outside"):
        _apply_result(tmp_path, result, _args(), _snapshot(tmp_path))


def test_apply_result_rejects_prefix_collision(tmp_path: Path) -> None:
    # A sibling directory whose path shares the same string prefix as tmp_path
    # (e.g. /tmp/abc vs /tmp/abcsibling) must be rejected, not accepted.
    sibling = tmp_path.parent / (tmp_path.name + "sibling")
    relative = Path("..") / sibling.name / "out.md"
    result = _make_result(str(relative), "evil")
    with pytest.raises(ValueError, match="Refusing to write outside"):
        _apply_result(tmp_path, result, _args(), _snapshot(tmp_path))


def test_apply_result_rejects_cross_track_path(tmp_path: Path) -> None:
    # A developer-audience file may not be written into the user track.
    result = _make_result("docs/user/index.md", "# Nope\n", audience="developer")
    with pytest.raises(ValueError, match="Refusing to write outside the developer track"):
        _apply_result(tmp_path, result, _args(), _snapshot(tmp_path))


def test_apply_result_rejects_unknown_audience(tmp_path: Path) -> None:
    result = _make_result("docs/user/index.md", "# Nope\n", audience="unknown")
    with pytest.raises(ValueError, match="unknown audience"):
        _apply_result(tmp_path, result, _args(), _snapshot(tmp_path))


def test_apply_result_redacts_model_echoed_secret(tmp_path: Path) -> None:
    leaked = "sk-ant-" + "A" * 24
    result = _make_result("docs/user/index.md", f"Set the key to {leaked}\n")
    _apply_result(tmp_path, result, _args(), _snapshot(tmp_path))
    written = (tmp_path / "docs" / "user" / "index.md").read_text(encoding="utf-8")
    assert leaked not in written
    assert "[REDACTED:anthropic-key]" in written


def test_apply_result_writes_manifest(tmp_path: Path) -> None:
    _apply_result(tmp_path, _make_result(), _args(), _snapshot(tmp_path))
    stored = manifest_module.read(tmp_path, "docs")
    assert stored is not None
    assert stored.tracks["user"]["files"][0]["path"] == "docs/user/index.md"
    assert stored.tracks["user"]["root"] == "docs/user"
    assert [entry.path for entry in stored.sources] == ["README.md"]


def test_check_reports_missing_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _run_check(tmp_path, "docs") == 1
    assert "Generate documentation first" in capsys.readouterr().err


def test_check_passes_then_detects_source_drift(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")
    _apply_result(tmp_path, _make_result(), _args(), _snapshot(tmp_path))

    assert _run_check(tmp_path, "docs") == 0

    (tmp_path / "README.md").write_text("# Test\n\nNew section.\n", encoding="utf-8")
    assert _run_check(tmp_path, "docs") == 1


def test_audience_resolution() -> None:
    assert audiences.resolve("both") == audiences.ALL
    assert audiences.resolve("user") == (audiences.USER,)
    assert audiences.resolve("developer") == (audiences.DEVELOPER,)
    with pytest.raises(ValueError):
        audiences.resolve("nobody")


def test_resolve_skill_root_uses_packaged_resources() -> None:
    skill_root = _resolve_skill_root()
    skill_text = skill_root.joinpath("SKILL.md").read_text(encoding="utf-8")
    assert "Update Docs Skill" in skill_text
