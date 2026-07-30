"""Guards on things that only break at build or install time.

Deliberately regex-based rather than tomllib-based: tomllib is 3.11+, and this
package supports 3.10, so a test that parsed pyproject.toml with it would fail on
the very floor it is meant to protect.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from claude_docsmith import __version__
from claude_docsmith.cli import _resolve_skill_root

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


def _pyproject_value(key: str) -> str:
    match = re.search(rf'^{key} = "([^"]+)"', PYPROJECT, re.MULTILINE)
    assert match, f"{key} not found in pyproject.toml"
    return match.group(1)


def test_version_is_consistent_across_all_three_manifests() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert _pyproject_value("version") == __version__
    assert plugin["version"] == __version__


def test_version_is_a_release_number() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), __version__


def test_requires_python_floor_matches_lowest_classifier() -> None:
    floor = _pyproject_value("requires-python").lstrip(">=")
    classifiers = re.findall(r'"Programming Language :: Python :: (\d+\.\d+)"', PYPROJECT)
    assert classifiers, "no per-version classifiers declared"
    assert min(classifiers, key=lambda v: tuple(int(p) for p in v.split("."))) == floor


def test_every_runtime_and_dev_dependency_is_bounded() -> None:
    """An unbounded floor is how ruff 0.16 broke CI on an unrelated commit."""
    requirements = re.findall(r'^\s+"([a-zA-Z0-9_.-]+[><=!,.0-9\s]*)",\s*$', PYPROJECT, re.MULTILINE)
    unbounded = [req for req in requirements if "<" not in req]
    assert unbounded == [], f"missing upper bound: {unbounded}"


def test_package_data_covers_every_packaged_skill_file() -> None:
    packaged = REPO_ROOT / "src" / "claude_docsmith" / "resources" / "update-docs"
    relative = sorted(
        path.relative_to(REPO_ROOT / "src" / "claude_docsmith").as_posix()
        for path in packaged.rglob("*")
        if path.is_file()
    )
    globs = re.findall(r'^\s+"(resources/[^"]+)",\s*$', PYPROJECT, re.MULTILINE)
    assert globs, "no resources globs in [tool.setuptools.package-data]"

    def covered(candidate: str) -> bool:
        return any(Path(candidate).match(pattern) for pattern in globs)

    assert [item for item in relative if not covered(item)] == []


def test_skill_root_uses_one_path_segment_per_joinpath() -> None:
    """Traversable.joinpath only accepts multiple segments from Python 3.11."""

    class SingleSegmentOnly:
        def __init__(self, parts: tuple[str, ...] = ()) -> None:
            self.parts = parts

        def joinpath(self, *segments: str) -> SingleSegmentOnly:
            if len(segments) != 1:
                raise TypeError("joinpath() takes exactly one argument on Python 3.10")
            return SingleSegmentOnly(self.parts + segments)

    import claude_docsmith.cli as cli_module

    original = cli_module.resources.files
    cli_module.resources.files = lambda _package: SingleSegmentOnly()  # type: ignore[assignment]
    try:
        root = _resolve_skill_root()
    finally:
        cli_module.resources.files = original  # type: ignore[assignment]
    assert root.parts == ("resources", "update-docs")  # type: ignore[attr-defined]


def test_console_script_entry_point_is_importable() -> None:
    target = _pyproject_value("claude-docsmith")
    module_path, _, attribute = target.partition(":")
    module = __import__(module_path, fromlist=[attribute])
    assert callable(getattr(module, attribute))


@pytest.mark.parametrize("relative", ["SKILL.md", "references/user-manual.md"])
def test_packaged_skill_is_readable_through_the_resource_api(relative: str) -> None:
    node = _resolve_skill_root()
    for segment in relative.split("/"):
        node = node.joinpath(segment)
    assert node.read_text(encoding="utf-8").strip()
