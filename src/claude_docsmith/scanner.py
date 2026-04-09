from __future__ import annotations

from pathlib import Path

from .models import RepoSnapshot, ScannedFile


DOC_CANDIDATES = [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "COPILOT.md",
    "docs",
]

CONFIG_CANDIDATES = [
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    ".github/workflows",
]

SOURCE_DIR_NAMES = {"src", "app", "backend", "frontend", "cmd", "internal", "tests"}
IGNORED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def scan_repository(root: Path, max_files: int = 40, max_bytes_per_file: int = 8000) -> RepoSnapshot:
    root = root.resolve()
    scanned_files: list[ScannedFile] = []
    inventory: list[str] = []

    for rel in DOC_CANDIDATES + CONFIG_CANDIDATES:
        path = root / rel
        if path.is_file():
            scanned_files.append(_read_file(root, path, "doc-or-config", max_bytes_per_file))
            inventory.append(_inventory_line(root, path))
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if len(scanned_files) >= max_files:
                    break
                if _should_skip(child):
                    continue
                if child.is_file():
                    scanned_files.append(_read_file(root, child, "doc-or-config", max_bytes_per_file))
                    inventory.append(_inventory_line(root, child))

    if len(scanned_files) < max_files:
        for child in sorted(root.rglob("*")):
            if len(scanned_files) >= max_files:
                break
            if _should_skip(child) or not child.is_file():
                continue
            rel_parts = child.relative_to(root).parts
            if not rel_parts:
                continue
            if rel_parts[0] not in SOURCE_DIR_NAMES:
                continue
            category = "test" if "tests" in rel_parts else "source"
            scanned_files.append(_read_file(root, child, category, max_bytes_per_file))
            inventory.append(_inventory_line(root, child))

    return RepoSnapshot(root=root, scanned_files=scanned_files, inventory=inventory)


def _read_file(root: Path, path: Path, category: str, max_bytes_per_file: int) -> ScannedFile:
    raw = path.read_bytes()[:max_bytes_per_file]
    text = raw.decode("utf-8", errors="replace")
    return ScannedFile(
        path=str(path.relative_to(root)),
        category=category,
        content=text,
    )


def _inventory_line(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    return str(relative)


def _should_skip(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)
