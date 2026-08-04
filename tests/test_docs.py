from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO = REPO_ROOT / "docs" / "demo.md"


def test_demo_screenshot_references_resolve() -> None:
    markdown = DEMO.read_text(encoding="utf-8")
    references = re.findall(r"!\[[^\]]+\]\(([^)]+)\)", markdown)

    assert references
    assert [reference for reference in references if not (DEMO.parent / reference).is_file()] == []


def test_demo_uses_the_reviewed_png_capture_set() -> None:
    markdown = DEMO.read_text(encoding="utf-8")
    references = {(DEMO.parent / reference).resolve() for reference in re.findall(r"!\[[^\]]+\]\(([^)]+)\)", markdown)}
    expected = {
        (DEMO.parent / "screenshots" / filename).resolve()
        for filename in ("install.png", "invoke.png", "review.png", "result.png")
    }

    assert references == expected
    for image in references:
        assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
