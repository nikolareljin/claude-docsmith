"""Guards on the GitHub Pages site.

The page is deployed straight from `site/`, so nothing else validates it: a stale
derived asset or a reference to a file that was never committed only shows up as
a broken published page.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE = REPO_ROOT / "site"
INDEX = SITE / "index.html"
HTML = INDEX.read_text(encoding="utf-8")


def test_site_index_exists_and_is_a_document() -> None:
    assert HTML.lstrip().lower().startswith("<!doctype html>")
    assert "<html lang=" in HTML


def test_small_size_mark_is_in_sync_with_the_logo() -> None:
    """site/logo-mark.svg is derived, not authored. Editing assets/logo.svg
    without re-running the script would ship a stale mark."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import render_site_mark

    expected = render_site_mark.render((REPO_ROOT / "assets" / "logo.svg").read_text(encoding="utf-8"))
    actual = (SITE / "logo-mark.svg").read_text(encoding="utf-8")
    assert actual == expected, "run: python3 scripts/render_site_mark.py"


def test_the_small_mark_drops_the_filters_that_swamp_it_at_small_sizes() -> None:
    mark = (SITE / "logo-mark.svg").read_text(encoding="utf-8")
    assert "url(#intenseGlow)" not in mark
    assert "url(#dropShadow)" not in mark


@pytest.mark.parametrize("attribute", ["href", "src"])
def test_every_local_reference_resolves(attribute: str) -> None:
    references = re.findall(rf'{attribute}="([^"#][^"]*)"', HTML)
    local = [
        ref
        for ref in references
        if not ref.startswith(("http://", "https://", "//", "mailto:", "data:"))
    ]
    missing = [ref for ref in local if not (SITE / ref).exists()]
    assert missing == [], missing


def test_the_forge_content_is_not_hidden_from_assistive_tech() -> None:
    """The track names and file lists live only inside the forge; hiding the
    whole subtree would drop the hero's substance for screen readers."""
    forge = HTML.split('<div class="forge"', 1)[1].split("</section>", 1)[0]
    assert 'class="forge" aria-hidden' not in HTML
    assert "docs/user/" in forge and "docs/developer/" in forge


def test_decorative_connectors_are_hidden_from_assistive_tech() -> None:
    assert 'class="forge__anvil" aria-hidden="true"' in HTML
    assert 'class="forge__fork"' in HTML
    fork_tag = HTML.split('<svg class="forge__fork"', 1)[1].split(">", 1)[0]
    assert 'aria-hidden="true"' in fork_tag


def test_the_page_does_not_advertise_a_pypi_install() -> None:
    assert "pipx install claude-docsmith" not in HTML
    assert "pypi.org/project/claude-docsmith" not in HTML


def test_pages_workflow_publishes_the_site_directory() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "actions/upload-pages-artifact" in workflow
    assert "path: site" in workflow


def test_documentation_image_references_resolve() -> None:
    missing: list[str] = []
    docs_root = (REPO_ROOT / "docs").resolve()
    for page in docs_root.rglob("*.md"):
        resolved_page = page.resolve()
        if not resolved_page.is_relative_to(docs_root) or not resolved_page.is_file():
            continue
        markdown = page.read_text(encoding="utf-8")
        for target in re.findall(r"!\[[^]]*\]\(([^)]+)\)", markdown):
            target = target.strip()
            if target.startswith("<") and ">" in target:
                target = target[1:target.index(">")]
            else:
                target = target.split(maxsplit=1)[0]
            if target.startswith(("http://", "https://", "data:")):
                continue
            resolved_target = (page.parent / target).resolve()
            if not resolved_target.is_relative_to(REPO_ROOT) or not resolved_target.is_file():
                missing.append(f"{page.relative_to(REPO_ROOT)} -> {target}")

    assert missing == []


def test_version_strings_in_docs_match_the_package() -> None:
    """The site and README bake in a version. Without this they quietly go stale
    one release after someone bumps the package -- the same class of wrong
    information as the PyPI install this release removed."""
    from claude_docsmith import __version__

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    stale = [
        f"{label}: {found}"
        for label, text in (("site/index.html", HTML), ("README.md", readme))
        for found in re.findall(r"claude-docsmith(?:\.git)?[ @](\d+\.\d+\.\d+)", text)
        if found != __version__
    ]
    assert stale == [], stale
