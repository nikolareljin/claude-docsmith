from pathlib import Path

import pytest

from claude_docsmith.cli import _apply_result, _resolve_skill_root
from claude_docsmith.models import GeneratedFile, GenerationResult


def _make_result(path: str = "docs/out.md", content: str = "# Hello\n") -> GenerationResult:
    return GenerationResult(
        summary="test summary",
        files=[GeneratedFile(path=path, audience="user", action="create", content=content)],
    )


def test_apply_result_writes_file(tmp_path: Path) -> None:
    result = _make_result("docs/out.md", "# Hello\n")
    _apply_result(tmp_path, result)
    out = tmp_path / "docs" / "out.md"
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("# Hello")


def test_apply_result_adds_trailing_newline(tmp_path: Path) -> None:
    result = _make_result("out.md", "no newline")
    _apply_result(tmp_path, result)
    assert (tmp_path / "out.md").read_text(encoding="utf-8").endswith("\n")


def test_apply_result_rejects_path_traversal(tmp_path: Path) -> None:
    result = _make_result("../../etc/passwd", "evil")
    with pytest.raises(ValueError, match="Refusing to write outside"):
        _apply_result(tmp_path, result)


def test_apply_result_rejects_prefix_collision(tmp_path: Path) -> None:
    # A sibling directory whose path shares the same string prefix as tmp_path
    # (e.g. /tmp/abc vs /tmp/abcsibling) must be rejected, not accepted.
    sibling = tmp_path.parent / (tmp_path.name + "sibling")
    relative = Path("..") / sibling.name / "out.md"
    result = _make_result(str(relative), "evil")
    with pytest.raises(ValueError, match="Refusing to write outside"):
        _apply_result(tmp_path, result)


def test_resolve_skill_root_uses_packaged_resources() -> None:
    skill_root = _resolve_skill_root()
    skill_text = skill_root.joinpath("SKILL.md").read_text(encoding="utf-8")
    assert "Update Docs Skill" in skill_text
