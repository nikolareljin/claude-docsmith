#!/usr/bin/env python3
"""Derive site/logo-mark.svg from assets/logo.svg.

The full mark carries an ambient heat circle and a two-stage Gaussian glow tuned
for 512px. At masthead and favicon sizes those swamp the artwork and it renders
as an orange blob, so the small-size variant drops them.

Run after editing assets/logo.svg:

    python3 scripts/render_site_mark.py
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "assets" / "logo.svg"
TARGET = REPO_ROOT / "site" / "logo-mark.svg"

# (find, replace) applied in order. Kept as plain substitutions so the test can
# re-derive the file and fail if the committed copy has drifted.
TRANSFORMS: tuple[tuple[str, str], ...] = (
    ('<circle cx="256" cy="270" r="160" fill="url(#heatGlow)" filter="url(#intenseGlow)" />', ""),
    ('<g transform="translate(268, 240)" filter="url(#intenseGlow)">', '<g transform="translate(268, 240)">'),
    ('<g filter="url(#dropShadow)">', "<g>"),
    ("<title id=\"title\">Claude Docsmith</title>", "<title id=\"title\">Claude Docsmith mark</title>"),
)


def render(source_svg: str) -> str:
    out = source_svg
    for find, replace in TRANSFORMS:
        out = out.replace(find, replace)
    return out


def main() -> int:
    TARGET.write_text(render(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"wrote {TARGET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
