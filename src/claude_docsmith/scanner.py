from __future__ import annotations

import os
from pathlib import Path

from .models import RepoSnapshot, ScannedFile
from .redaction import Finding, is_sensitive_path, redact

DOC_CANDIDATES = [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "COPILOT.md",
    "ABOUT.md",
    "CHANGELOG.md",
    "docs",
]

CONFIG_CANDIDATES = [
    "package.json",
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "CMakeLists.txt",
    "Makefile",
    "tsconfig.json",
    ".eslintrc.json",
    ".eslintrc.js",
    "jest.config.js",
    "jest.config.ts",
    ".env.example",
    "env.example",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    ".github/workflows",
]

SOURCE_DIR_NAMES = {
    "src", "app", "backend", "frontend", "cmd", "internal",
    "lib", "pkg", "packages", "api", "services", "core",
    "controllers", "handlers", "routes", "models", "views",
    "tests", "test", "spec", "__tests__",
}

TEST_DIR_NAMES = {"tests", "test", "spec", "__tests__"}

IGNORED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    "dist", "build", "target", "vendor", ".next", ".nuxt",
    "coverage", ".tox", "htmlcov", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "out", "bin", "obj",
}

# Build metadata directories are named after the package, so they cannot be
# matched by name. An editable install leaves one under src/, where PKG-INFO
# duplicates the whole README and the sibling files burn scan slots that should
# go to source.
IGNORED_DIR_SUFFIXES = (".egg-info", ".dist-info", ".egg")

IMAGE_ROOTS = ("docs", "assets", "screenshots", ".github", "static", "public")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
DEFAULT_MAX_IMAGES = 200
IMAGE_SCAN_MULTIPLIER = 10


def _is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIRS or name.endswith(IGNORED_DIR_SUFFIXES)


_LANGUAGE_MANIFEST_MAP: dict[str, str] = {
    "pyproject.toml": "python",
    "setup.py": "python",
    "requirements.txt": "python",
    "package.json": "node",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "composer.json": "php",
    "Gemfile": "ruby",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "CMakeLists.txt": "cpp",
}


def scan_repository(
    root: Path,
    max_files: int = 40,
    max_bytes_per_file: int = 8000,
    max_context_bytes: int = 128 * 1024,
    skip_tests: bool = False,
    redact_secrets: bool = True,
    max_images: int = DEFAULT_MAX_IMAGES,
) -> RepoSnapshot:
    root = root.resolve()
    scanned_files: list[ScannedFile] = []
    inventory: list[str] = []
    redactions: list[Finding] = []
    skipped_sensitive: list[str] = []
    total_bytes = 0
    image_inventory = _discover_images(root, max_images=max_images)

    def _add(path: Path, category: str) -> bool:
        nonlocal total_bytes
        if path.suffix.lower() in IMAGE_SUFFIXES:
            return True
        if len(scanned_files) >= max_files:
            return False
        if skip_tests and category == "test":
            return True
        rel = path.relative_to(root).as_posix()
        if is_sensitive_path(rel):
            skipped_sensitive.append(rel)
            return True
        remaining_budget = max_context_bytes - total_bytes
        if remaining_budget <= 0:
            return False
        try:
            with path.open("rb") as fh:
                raw = fh.read(min(max_bytes_per_file, remaining_budget))
        except OSError:
            return True
        chunk = len(raw)
        total_bytes += chunk
        text = raw.decode("utf-8", errors="replace")
        if redact_secrets:
            text, findings = redact(text, path=rel)
            redactions.extend(findings)
        scanned_files.append(ScannedFile(path=rel, category=category, content=text))
        inventory.append(rel)
        return True

    for rel in DOC_CANDIDATES + CONFIG_CANDIDATES:
        path = root / rel
        if _is_safe_file(path, root):
            if not _add(path, "doc-or-config"):
                break
        elif _is_safe_dir(path, root):
            budget_hit = False
            for child in _walk_files(path, skip_tests=skip_tests):
                if _should_skip(child, root) or not _is_safe_file(child, root):
                    continue
                if not _add(child, "doc-or-config"):
                    budget_hit = True
                    break
            if budget_hit:
                break

    if len(scanned_files) < max_files and total_bytes < max_context_bytes:
        for child in _walk_files(root, skip_tests=skip_tests):
            if _should_skip(child, root) or not _is_safe_file(child, root):
                continue
            rel_parts = child.relative_to(root).parts
            if not rel_parts or rel_parts[0] not in SOURCE_DIR_NAMES:
                continue
            category = "test" if any(p in TEST_DIR_NAMES for p in rel_parts) else "source"
            if not _add(child, category):
                break

    detected_language = _detect_language(root)
    return RepoSnapshot(
        root=root,
        scanned_files=scanned_files,
        inventory=inventory,
        detected_language=detected_language,
        total_bytes=total_bytes,
        redactions=redactions,
        skipped_sensitive=sorted(set(skipped_sensitive)),
        image_inventory=image_inventory,
    )


def _discover_images(root: Path, *, max_images: int = DEFAULT_MAX_IMAGES) -> list[str]:
    """Return a bounded, stable inventory of safe image assets without reading them."""
    if max_images <= 0:
        return []

    discovered: set[str] = set()
    scanned_paths = 0
    max_scanned_paths = max_images * IMAGE_SCAN_MULTIPLIER
    for relative_root in IMAGE_ROOTS:
        candidate = root / relative_root
        if not _is_safe_dir(candidate, root):
            continue
        for path in _walk_files(candidate):
            scanned_paths += 1
            if scanned_paths > max_scanned_paths:
                return sorted(discovered)
            if path.suffix.lower() not in IMAGE_SUFFIXES or not _is_safe_file(path, root):
                continue
            relative_path = path.relative_to(root).as_posix()
            if is_sensitive_path(relative_path):
                continue
            discovered.add(relative_path)
            if len(discovered) >= max_images:
                return sorted(discovered)
    return sorted(discovered)


def _detect_language(root: Path) -> str:
    for manifest, lang in _LANGUAGE_MANIFEST_MAP.items():
        if (root / manifest).is_file():
            return lang
    return "unknown"


def _walk_files(root: Path, *, skip_tests: bool = False):
    for current_root, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current_root)
        pruned_dirs = (
            dirname for dirname in dirnames
            if not _is_ignored_dir(dirname) and (not skip_tests or dirname not in TEST_DIR_NAMES)
        )
        dirnames[:] = sorted(pruned_dirs)
        filenames.sort()
        for filename in filenames:
            yield current_path / filename


def _should_skip(path: Path, root: Path) -> bool:
    return any(_is_ignored_dir(part) for part in path.relative_to(root).parts)


def _is_safe_file(path: Path, root: Path) -> bool:
    """Return True only if path is a regular file that resolves within root."""
    try:
        resolved = path.resolve()
    except OSError:
        return False

    try:
        resolved.relative_to(root)
    except ValueError:
        return False

    return resolved.is_file()


def _is_safe_dir(path: Path, root: Path) -> bool:
    """Return True only if path is a directory that resolves within root."""
    try:
        resolved = path.resolve()
    except OSError:
        return False

    try:
        resolved.relative_to(root)
    except ValueError:
        return False

    return resolved.is_dir()
