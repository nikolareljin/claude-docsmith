from pathlib import Path

from claude_docsmith import audiences
from claude_docsmith.models import RepoSnapshot, ScannedFile
from claude_docsmith.prompting import MAX_PROMPT_IMAGES, build_prompt
from claude_docsmith.redaction import Finding


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
    prompt = build_prompt(_make_snapshot(tmp_path), _skill_root(), audiences.USER)
    assert '"summary"' in prompt
    assert '"files"' in prompt


def test_build_prompt_contains_inventory(tmp_path: Path) -> None:
    prompt = build_prompt(_make_snapshot(tmp_path), _skill_root(), audiences.USER)
    assert "README.md" in prompt


def test_build_prompt_contains_language(tmp_path: Path) -> None:
    prompt = build_prompt(_make_snapshot(tmp_path), _skill_root(), audiences.USER)
    assert "python" in prompt


def test_build_prompt_skip_checklists(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    full = build_prompt(snapshot, _skill_root(), audiences.USER, skip_checklists=False)
    slim = build_prompt(snapshot, _skill_root(), audiences.USER, skip_checklists=True)
    assert len(slim) < len(full)


def test_build_prompt_empty_snapshot(tmp_path: Path) -> None:
    snapshot = RepoSnapshot(root=tmp_path, scanned_files=[], inventory=[])
    prompt = build_prompt(snapshot, _skill_root(), audiences.USER)
    assert "Return JSON only" in prompt


def test_each_track_loads_only_its_own_reference(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    user = build_prompt(snapshot, _skill_root(), audiences.USER)
    developer = build_prompt(snapshot, _skill_root(), audiences.DEVELOPER)

    assert "# User Manual Reference" in user
    assert "# Screenshot Capture Reference" in user
    assert "# Developer Reference" not in user
    assert "# Developer Documentation Checklist" not in user

    assert "# Developer Reference" in developer
    assert "# User Manual Reference" not in developer
    assert "# Screenshot Capture Reference" not in developer
    assert "# User Documentation Checklist" not in developer


def test_prompt_pins_output_root_per_track(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    user = build_prompt(snapshot, _skill_root(), audiences.USER, docs_dir="documentation")
    developer = build_prompt(snapshot, _skill_root(), audiences.DEVELOPER, docs_dir="documentation")
    assert "documentation/user/**" in user
    assert "documentation/developer/**" in developer


def test_prompt_warns_about_redaction_markers(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    snapshot.redactions = [Finding(path="src/app.py", line=3, kind="anthropic-key")]
    snapshot.skipped_sensitive = [".env"]
    prompt = build_prompt(snapshot, _skill_root(), audiences.DEVELOPER)
    assert "Security notice" in prompt
    assert "deliberately not read: .env" in prompt


def test_existing_images_are_listed_only_for_the_user_track(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    snapshot.image_inventory = ["assets/dashboard.png", "docs/screenshots/login.webp"]

    user = build_prompt(snapshot, _skill_root(), audiences.USER)
    developer = build_prompt(snapshot, _skill_root(), audiences.DEVELOPER)

    assert "Existing repository image assets:" in user
    assert "assets/dashboard.png" in user
    assert "docs/screenshots/login.webp" in user
    assert "Existing repository image assets:" not in developer
    assert "assets/dashboard.png" not in developer


def test_existing_images_are_bounded_in_the_user_prompt(tmp_path: Path) -> None:
    snapshot = _make_snapshot(tmp_path)
    snapshot.image_inventory = [
        f"assets/image-{index:03}.png" for index in range(MAX_PROMPT_IMAGES + 2)
    ]

    prompt = build_prompt(snapshot, _skill_root(), audiences.USER)

    assert f"assets/image-{MAX_PROMPT_IMAGES - 1:03}.png" in prompt
    assert f"assets/image-{MAX_PROMPT_IMAGES:03}.png" not in prompt
    assert "2 more image asset(s) omitted" in prompt
