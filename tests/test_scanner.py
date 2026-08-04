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


def test_byte_limit_truncates_follow_up_file_to_remaining_budget(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "large.md").write_text("L" * 900, encoding="utf-8")
    (tmp_path / "docs" / "small.md").write_text("small\n", encoding="utf-8")

    snapshot = scan_repository(tmp_path, max_files=10, max_bytes_per_file=900, max_context_bytes=905)

    scanned_paths = [item.path for item in snapshot.scanned_files]
    assert "docs/large.md" in scanned_paths
    assert "docs/small.md" in scanned_paths
    assert snapshot.total_bytes == 905


def test_skip_tests_excludes_test_files(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_foo.py").write_text("def test_foo(): pass\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass\n", encoding="utf-8")
    snapshot = scan_repository(tmp_path, skip_tests=True)
    categories = {f.category for f in snapshot.scanned_files}
    assert "test" not in categories


def test_skip_tests_avoids_descending_into_test_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_foo.py").write_text("def test_foo(): pass\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass\n", encoding="utf-8")

    original_walk = __import__("os").walk

    def fake_walk(root, topdown=True):  # type: ignore[no-untyped-def]
        for current_root, dirnames, filenames in original_walk(root, topdown=topdown):
            assert Path(current_root).name != "tests"
            yield current_root, dirnames, filenames

    monkeypatch.setattr("claude_docsmith.scanner.os.walk", fake_walk)

    snapshot = scan_repository(tmp_path, skip_tests=True)

    scanned_paths = {item.path for item in snapshot.scanned_files}
    assert "src/main.py" in scanned_paths
    assert not any(path.startswith("tests/") for path in scanned_paths)


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


def test_symlinked_candidate_directory_outside_root_is_not_walked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external_root = tmp_path.parent / f"{tmp_path.name}-external-docs"
    external_root.mkdir()
    docs_link = tmp_path / "docs"
    try:
        docs_link.symlink_to(external_root, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    walked_roots: list[Path] = []
    original_walk = __import__("os").walk

    def fake_walk(root, *args, **kwargs):  # type: ignore[no-untyped-def]
        walked_roots.append(Path(root).resolve())
        yield from original_walk(root, *args, **kwargs)

    monkeypatch.setattr("claude_docsmith.scanner.os.walk", fake_walk)

    scan_repository(tmp_path, max_files=10, max_bytes_per_file=1024)

    assert external_root.resolve() not in walked_roots


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


def test_inventory_paths_use_posix_separators(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    guide = docs / "guide.md"
    guide.write_text("guide\n", encoding="utf-8")

    original_relative_to = Path.relative_to

    class FakeRelativePath:
        def __init__(self, value: str) -> None:
            self._value = value
            self.parts = ("docs", "guide.md")

        def as_posix(self) -> str:
            return "docs/guide.md"

        def __str__(self) -> str:
            return self._value

    def fake_relative_to(self: Path, *other):  # type: ignore[no-untyped-def]
        if self == guide:
            return FakeRelativePath("docs\\guide.md")
        return original_relative_to(self, *other)

    monkeypatch.setattr(Path, "relative_to", fake_relative_to)

    snapshot = scan_repository(tmp_path, max_files=10, max_bytes_per_file=1024)

    assert "docs/guide.md" in snapshot.inventory
    assert "docs\\guide.md" not in snapshot.inventory


def test_sensitive_files_are_never_scanned(tmp_path: Path) -> None:
    # Planted inside a source directory, which the scanner does walk, so the
    # deny list is what excludes them rather than the candidate list.
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("ANTHROPIC_API_KEY=your-key-here\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / ".env").write_text("ANTHROPIC_API_KEY=sk-ant-" + "A" * 24 + "\n", encoding="utf-8")
    (src / "server.pem").write_text("-----BEGIN PRIVATE KEY-----\nnotarealkey\n", encoding="utf-8")
    (src / "app.py").write_text("x = 1\n", encoding="utf-8")

    snapshot = scan_repository(tmp_path, max_files=20, max_bytes_per_file=4096)

    assert "src/.env" not in snapshot.inventory
    assert "src/server.pem" not in snapshot.inventory
    assert snapshot.skipped_sensitive == ["src/.env", "src/server.pem"]
    assert "src/app.py" in snapshot.inventory
    assert ".env.example" in snapshot.inventory
    joined = "\n".join(item.content for item in snapshot.scanned_files)
    assert "sk-ant-" not in joined
    assert "notarealkey" not in joined


def test_secrets_in_scanned_sources_are_redacted(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    leaked = "ghp_" + "C" * 36
    (src / "client.py").write_text(f'TOKEN = "{leaked}"\n', encoding="utf-8")

    snapshot = scan_repository(tmp_path, max_files=20, max_bytes_per_file=4096)

    joined = "\n".join(item.content for item in snapshot.scanned_files)
    assert leaked not in joined
    assert "[REDACTED:github-token]" in joined
    assert [finding.kind for finding in snapshot.redactions] == ["github-token"]


def test_redaction_can_be_disabled(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    leaked = "ghp_" + "C" * 36
    (src / "client.py").write_text(f'TOKEN = "{leaked}"\n', encoding="utf-8")

    snapshot = scan_repository(tmp_path, max_files=20, max_bytes_per_file=4096, redact_secrets=False)

    joined = "\n".join(item.content for item in snapshot.scanned_files)
    assert leaked in joined
    assert snapshot.redactions == []


def test_build_metadata_directories_are_not_scanned(tmp_path: Path) -> None:
    """An editable install leaves *.egg-info under src/, and its PKG-INFO
    duplicates the entire README into the prompt."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Real readme\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("x = 1\n", encoding="utf-8")
    for name in ("demo.egg-info", "demo.dist-info", "demo.egg"):
        meta = src / name
        meta.mkdir()
        (meta / "PKG-INFO").write_text("# Real readme\n(duplicated)\n", encoding="utf-8")

    snapshot = scan_repository(tmp_path, max_files=40, max_bytes_per_file=8000)

    assert "src/app.py" in snapshot.inventory
    assert not [path for path in snapshot.inventory if ".egg-info" in path]
    assert not [path for path in snapshot.inventory if ".dist-info" in path]
    joined = "\n".join(item.content for item in snapshot.scanned_files)
    assert joined.count("# Real readme") == 1


def test_image_inventory_is_sorted_deduplicated_and_separate_from_text(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    nested = docs / "screenshots"
    nested.mkdir(parents=True)
    assets = tmp_path / "assets"
    assets.mkdir()
    public = tmp_path / "public"
    public.mkdir()

    (nested / "z-screen.PNG").write_bytes(b"\x89PNG\r\n\x1a\nnot-text")
    (assets / "a-screen.webp").write_bytes(b"RIFFnot-text")
    (public / "ignored.txt").write_text("text\n", encoding="utf-8")
    (docs / "guide.md").write_text("guide\n", encoding="utf-8")

    snapshot = scan_repository(tmp_path, max_files=1, max_context_bytes=5)

    assert snapshot.image_inventory == [
        "assets/a-screen.webp",
        "docs/screenshots/z-screen.PNG",
    ]
    assert [item.path for item in snapshot.scanned_files] == ["docs/guide.md"]
    assert snapshot.total_bytes == 5
    assert not set(snapshot.image_inventory) & set(snapshot.inventory)


@pytest.mark.parametrize("suffix", [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"])
def test_image_inventory_supports_documented_extensions(tmp_path: Path, suffix: str) -> None:
    static = tmp_path / "static"
    static.mkdir()
    image = static / f"feature{suffix}"
    image.write_bytes(b"image")

    snapshot = scan_repository(tmp_path)

    assert snapshot.image_inventory == [f"static/feature{suffix}"]


def test_image_inventory_rejects_symlinked_files_outside_root(tmp_path: Path) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-external-image.png"
    external.write_bytes(b"image")
    assets = tmp_path / "assets"
    assets.mkdir()
    link = assets / "external.png"
    try:
        link.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    snapshot = scan_repository(tmp_path)

    assert snapshot.image_inventory == []


def test_image_inventory_honors_configured_limit(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    for index in range(5):
        (assets / f"image-{index}.png").write_bytes(b"image")

    snapshot = scan_repository(tmp_path, max_images=3)

    assert snapshot.image_inventory == [
        "assets/image-0.png",
        "assets/image-1.png",
        "assets/image-2.png",
    ]


def test_zero_image_limit_skips_discovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "image.png").write_bytes(b"image")

    def fail_walk(*args, **kwargs):  # type: ignore[no-untyped-def]
        pytest.fail("image discovery should not walk files when max_images is zero")

    monkeypatch.setattr("claude_docsmith.scanner._walk_files", fail_walk)

    snapshot = scan_repository(tmp_path, max_files=0, max_images=0)

    assert snapshot.image_inventory == []


def test_image_inventory_excludes_sensitive_filenames(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "secrets.png").write_bytes(b"image")
    (assets / "diagram.png").write_bytes(b"image")

    snapshot = scan_repository(tmp_path)

    assert snapshot.image_inventory == ["assets/diagram.png"]


def test_text_scan_stops_before_walking_images_when_file_budget_is_exhausted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "README.md").write_text("readme\n", encoding="utf-8")
    (docs / "image.png").write_bytes(b"image")

    original_walk = __import__("os").walk

    def guarded_walk(root, *args, **kwargs):  # type: ignore[no-untyped-def]
        if Path(root) == docs:
            pytest.fail("text scan should stop before walking docs when max_files is reached")
        yield from original_walk(root, *args, **kwargs)

    monkeypatch.setattr("claude_docsmith.scanner.os.walk", guarded_walk)

    snapshot = scan_repository(tmp_path, max_files=1, max_images=0)

    assert snapshot.inventory == ["README.md"]


@pytest.mark.parametrize("target_name", ["secrets.png", "secrets.txt"])
def test_image_inventory_validates_internal_symlink_targets(
    tmp_path: Path, target_name: str
) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    target = tmp_path / target_name
    target.write_bytes(b"not-safe-inventory-content")
    link = assets / "safe-looking.png"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    snapshot = scan_repository(tmp_path)

    assert snapshot.image_inventory == []


def test_image_scan_budget_does_not_starve_later_roots(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    for index in range(11):
        (docs / f"document-{index}.txt").write_text("text\n", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "diagram.png").write_bytes(b"image")

    snapshot = scan_repository(tmp_path, max_files=0, max_images=1)

    assert snapshot.image_inventory == ["assets/diagram.png"]
