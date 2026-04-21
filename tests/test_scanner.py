from pathlib import Path

import pytest

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


def test_detected_language_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    snapshot = scan_repository(tmp_path)
    assert snapshot.detected_language == "python"


def test_detected_language_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"x"}', encoding="utf-8")
    snapshot = scan_repository(tmp_path)
    assert snapshot.detected_language == "node"


def test_detected_language_unknown(tmp_path: Path) -> None:
    snapshot = scan_repository(tmp_path)
    assert snapshot.detected_language == "unknown"


def test_byte_limit_stops_scan(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    for i in range(10):
        (tmp_path / "src" / f"file{i}.py").write_text("x" * 1000, encoding="utf-8")
    snapshot = scan_repository(tmp_path, max_context_bytes=3000, max_bytes_per_file=1000)
    assert snapshot.total_bytes <= 3000


def test_skip_tests_excludes_test_files(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("def test_foo(): pass\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass\n", encoding="utf-8")
    snapshot = scan_repository(tmp_path, skip_tests=True)
    categories = {f.category for f in snapshot.scanned_files}
    assert "test" not in categories


def test_ignored_dirs_skipped(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("module.exports={}", encoding="utf-8")
    snapshot = scan_repository(tmp_path)
    scanned_paths = {item.path for item in snapshot.scanned_files}
    assert not any("node_modules" in p for p in scanned_paths)


def test_symlinked_directory_outside_root_is_skipped(tmp_path: Path) -> None:
    external_root = tmp_path.parent / f"{tmp_path.name}-external"
    external_root.mkdir()
    (external_root / "secret.md").write_text("do not scan\n", encoding="utf-8")

    docs_link = tmp_path / "docs"
    try:
        docs_link.symlink_to(external_root, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    snapshot = scan_repository(tmp_path, max_files=10, max_bytes_per_file=1024)
    scanned_paths = {item.path for item in snapshot.scanned_files}
    assert "docs/secret.md" not in scanned_paths


def test_unreadable_file_is_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    unreadable = docs / "secret.md"
    unreadable.write_text("secret\n", encoding="utf-8")
    readable = docs / "guide.md"
    readable.write_text("guide\n", encoding="utf-8")

    original_open = Path.open

    def fake_open(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self == unreadable:
            raise PermissionError("permission denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fake_open)

    snapshot = scan_repository(tmp_path, max_files=10, max_bytes_per_file=1024)
    scanned_paths = {item.path for item in snapshot.scanned_files}
    assert "docs/secret.md" not in scanned_paths
    assert "docs/guide.md" in scanned_paths
