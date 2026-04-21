from pathlib import Path


def test_packaged_skill_resources_match_source_skill_files() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "skills" / "update-docs"
    packaged_root = repo_root / "src" / "claude_docsmith" / "resources" / "update-docs"

    source_files = sorted(path.relative_to(source_root) for path in source_root.rglob("*") if path.is_file())
    packaged_files = sorted(path.relative_to(packaged_root) for path in packaged_root.rglob("*") if path.is_file())

    assert packaged_files == source_files

    for relative_path in source_files:
      assert (packaged_root / relative_path).read_text(encoding="utf-8") == (
          source_root / relative_path
      ).read_text(encoding="utf-8")
