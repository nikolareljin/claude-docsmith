from pathlib import Path

from claude_docsmith.scanner import scan_repository


def test_scanner_collects_docs_and_source(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "developer-guide.md").write_text("dev docs\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    snapshot = scan_repository(tmp_path, max_files=10, max_bytes_per_file=1024)

    scanned_paths = {item.path for item in snapshot.scanned_files}
    assert "README.md" in scanned_paths
    assert "docs/developer-guide.md" in scanned_paths
    assert "src/main.py" in scanned_paths
