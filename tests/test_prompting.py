from pathlib import Path

from claude_docsmith.models import RepoSnapshot, ScannedFile
from claude_docsmith.prompting import build_prompt


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / "update-docs"


def _make_snapshot(tmp_path: Path) -> RepoSnapshot:
    f = ScannedFile(path="README.md", category="doc-or-config", content="# Test\n")
    return RepoSnapshot(
        root=tmp_path,
        scanned_files=[f],
        inventory=["README.md"],
        detected_language="python",
        total_bytes=9,
    )


def test_build_prompt_contains_json_hint(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    prompt = build_prompt(snapshot, _skill_root())
    assert '"summary"' in prompt
    assert '"files"' in prompt


def test_build_prompt_contains_inventory(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    prompt = build_prompt(snapshot, _skill_root())
    assert "README.md" in prompt


def test_build_prompt_contains_language(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    prompt = build_prompt(snapshot, _skill_root())
    assert "python" in prompt


def test_build_prompt_skip_checklists(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    full = build_prompt(snapshot, _skill_root(), skip_checklists=False)
    slim = build_prompt(snapshot, _skill_root(), skip_checklists=True)
    assert len(slim) < len(full)


def test_build_prompt_empty_snapshot(tmp_path: Path) -> None:
    snapshot = RepoSnapshot(root=tmp_path, scanned_files=[], inventory=[])
    prompt = build_prompt(snapshot, _skill_root())
    assert "Return JSON only" in prompt
