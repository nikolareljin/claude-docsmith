# Changelog

All notable changes to claude-docsmith are documented here.

## [1.3.0] - 2026-08-03

### Added

- Repository image discovery for PNG, JPEG, GIF, WebP, and SVG assets under common
  documentation and asset directories. The user-documentation prompt receives a stable,
  deduplicated inventory without reading binary content.
- A screenshot capture workflow for browser, Android, Apple, terminal, and desktop
  interfaces. It reuses current images, requests approval for the target and shot list,
  captures key states with locally available tools, and inspects every result before use.
- A stable `docs/user/screenshots/manifest.yml` contract for present and missing shots,
  including descriptive alt text, reproduction steps, and actionable blockers.

### Changed

- Binary images no longer consume text scan slots or context bytes.
- Missing screenshots render as visible callouts instead of broken image references.
- Plugin usage examples now use the registered namespaced slash command; the previous
  short form was not recognised by a locally loaded plugin.
- Screenshot capture continues documentation updates when no suitable local target is
  available and never reports an unavailable capture as completed.

### Security

- Physical devices, windows, and desktop regions require explicit approval before capture.
- Captures use controlled demo data; images containing credentials, personal information,
  account details, or device identifiers must be recaptured before they enter documentation.

### Tests

- Added coverage for image formats, stable ordering, deduplication, scan-budget isolation,
  symlink containment, audience-specific prompting, and packaged skill parity.

[1.3.0]: https://github.com/nikolareljin/claude-docsmith/compare/1.1.1...1.3.0

---


## [1.1.1] - 2026-07-30
### Fixed

- **`Release Tag` workflow failed to start.** It called `ci-helpers`'
  `auto-tag-release.yml`, which declares `actions: write` for its dispatch job. GitHub
  validates a reusable workflow's declared permissions at startup regardless of any `if:`
  gate, so the run failed before it began and the `1.1.0` tag was never created. This
  repository does not use auto-dispatch, so it now calls the least-privilege `auto-tag.yml`,
  which needs exactly the permissions already granted.
- **README advertised a PyPI package that does not exist.** The version and Python badges
  rendered "package or version not found", and `pipx install claude-docsmith` /
  `pip install --user claude-docsmith` would both 404. Badges now come from the git tag and
  from `requires-python`; install instructions point at the repository, with a note on
  pinning a released tag.

### Added

- **Documentation site** at [nikolareljin.github.io/claude-docsmith](https://nikolareljin.github.io/claude-docsmith/):
  what the two tracks are, both install paths, and a worked standalone run against Ollama.
  Source in `site/`, deployed from `main` by `.github/workflows/pages.yml`.

### Fixed

- **The site's hero was hidden from assistive tech.** The forge diagram carried
  `aria-hidden="true"`, and the two track names and their file lists appear nowhere else on
  the page, so screen readers got nothing from it. Only the decorative connector and strike
  rule are hidden now.
- **The favicon used the full mark.** Its ambient glow is tuned for 512px and renders as a
  blob at favicon size; it now uses the small-size variant, as the masthead already did.

### Build

- `site/logo-mark.svg` is derived from `assets/logo.svg` by
  `scripts/render_site_mark.py` instead of being a hand-edited copy, and a test fails if the
  committed file drifts from the source. The unguarded byte-identical `site/logo.svg` copy is
  gone.
- New `tests/test_site.py`: the derived mark stays in sync, every local `href`/`src` in the
  page resolves, the hero stays readable by assistive tech, the page never advertises a PyPI
  install, and the version strings baked into the site and README match `__version__` — the
  same class of stale information this release removed.
- CI lints and byte-compiles `scripts/` alongside `src` and `tests`.
- `vendor/script-helpers` submodule advanced to `0.19.0` (the current `production`).
  `ci-helpers` `production` is `0.18.0` and already current.

[1.1.1]: https://github.com/nikolareljin/claude-docsmith/compare/1.1.0...1.1.1

---

## [1.1.0] - 2026-07-30

### Added

- **Two-track generation** (#4). `--audience user|developer|both` (default `both`). Each track
  gets its own prompt and its own provider call, so a complete user manual and a complete
  developer reference no longer compete for a single output token budget.
- **Audience-scoped output trees**. Generated files are written to `docs/user/**` and
  `docs/developer/**`; a file outside its own track's root is rejected. The user track may
  additionally write `README.md`. New `--docs-dir` flag relocates the documentation root.
- **Secret redaction** (#5). A sensitive-filename deny list keeps `.env`, private keys,
  keystores, `.netrc`, `.npmrc`, `.pypirc`, credential stores, and Terraform state from being
  read at all. Credential-shaped values in files that are read are replaced with
  `[REDACTED:<kind>]` markers, inbound (before prompting) and outbound (before `--apply`
  writes). Findings record `path`, `line`, and `kind` only — never the value.
  `--fail-on-secret` exits `2`; `--no-redact` disables content scrubbing but not the deny list.
- **Documentation manifest and drift gate** (#6). `--apply` writes
  `docs/.docsmith/manifest.json` recording every generated page, its track, and the hash of
  every source it was derived from. `--check` re-scans and exits `1` on drift, `0` when
  current, with no network request — usable as a CI freshness gate.
- **Per-audience skill references** (#7). `SKILL.md` is now an orchestrator routing to
  `references/user-manual.md` and `references/developer-reference.md`, plus page templates
  under `templates/pages/`. Each track loads only its own reference and checklist.
- `--version` flag.
- Project logo. `assets/logo.svg` (square mark) and `assets/logo-hero.svg` (wide banner with
  wordmark) are the vector sources, with rendered PNGs alongside. The README leads with the
  hero. Absolute URL and PNG on purpose: the README is also the PyPI long description, which
  cannot resolve relative paths and does not render SVG.

### Changed

- **No model identifier is hardcoded any more.** A pinned default goes stale on every model
  release, and for Ollama it named a model the user may never have pulled. The model is now
  resolved as `--model` > `DOCSMITH_<PROVIDER>_MODEL` > `DOCSMITH_MODEL` > provider discovery
  (`GET /api/tags` for Ollama, newest by `created_at` from `GET /v1/models` for Claude). The
  resolved name is printed to stderr when it was not given explicitly; if discovery cannot
  run the tool exits 1 with guidance rather than guessing.
  A unit test fails the build if a model name reappears in `src/claude_docsmith/*.py`.
- Claude API `max_tokens` raised from 8192 to 16000, and the default `--timeout` from 180 to
  300 seconds, to accommodate longer per-track responses.
- `--dry-run` prints one prompt per selected track under an `=== AUDIENCE: <track> ===`
  separator, each with its own context stats.
- The `audience` field on generated files is now set from the track that produced the file
  rather than taken from the model's own label.

### Security

- **`--check` treats the manifest as untrusted input.** `docs/.docsmith/manifest.json` lives
  in the repository being checked, and `--check` is meant to be safe to run in CI against code
  the operator does not control. Doc-entry paths were joined onto the repo root and read
  directly, so an absolute path, a `..` segment or a symlink made the check stat and hash
  files anywhere on the machine; missing or non-string keys raised an uncaught `KeyError`.
  Paths are now resolved and confirmed to stay inside the repository, entries are type-checked,
  and anything unusable is reported as drift under a new `invalid_entries` bucket instead of
  being read.
- **Scan settings replayed from the manifest are clamped.** `--check` fed `max_files`,
  `max_bytes_per_file` and `max_context_kb` straight into the scanner, so a crafted value
  turned a cheap offline check into reading the whole repository into memory. `--check` also
  now takes `docs_dir` from the command line rather than from the file.
- **A malformed manifest can no longer crash `read()`.** Non-dict payloads, wrong-typed
  `tracks`/`sources`/`scan`/`redactions`, and non-string metadata are rejected or coerced
  rather than raising.

### Fixed

- **`--apply` no longer writes a partial documentation tree.** Validation and writing were
  interleaved, so a rejected path partway down the file list left the earlier files on disk
  with no manifest and a traceback. All files are now validated and scrubbed before any of
  them is written.
- **Build metadata directories are no longer scanned.** An editable install leaves
  `<package>.egg-info/` under `src/`, whose `PKG-INFO` duplicates the entire README into the
  prompt while its five sibling files consume scan slots that should go to source — on this
  repository, 6 of 40 slots against a context budget that was already saturated. `IGNORED_DIRS`
  matches exact names, so suffix matching was added for `.egg-info`, `.dist-info` and `.egg`
  (and `.ruff_cache` by name).
- **The package was broken on Python 3.10**, the version `requires-python` declares as the
  floor. `_resolve_skill_root` called `Traversable.joinpath("resources", "update-docs")`, and
  multiple path segments per call are only accepted from Python 3.11 — on 3.10 every run
  raised `TypeError`. Now one segment per call, with a regression test that rejects
  multi-segment usage.

### Build

- Every runtime and dev dependency now carries an upper bound (`httpx>=0.27,<1.0`,
  `ruff>=0.16,<0.17`, `pytest>=8.0,<10.0`, `build>=1.2.2,<2.0`, `setuptools>=68,<82`).
  Dropped the redundant `wheel` build requirement. A test fails the build if an unbounded
  requirement is added.
- CI now runs the full matrix the classifiers advertise — 3.10, 3.11, 3.12 — instead of 3.11
  alone, plus a `package` job that builds the sdist and wheel and smoke-tests the CLI
  installed from each.
- Added packaging guards: the version must agree across `pyproject.toml`, `plugin.json` and
  `__init__.py`; the `requires-python` floor must match the lowest classifier; the
  `package-data` globs must cover every packaged skill file.
- Pinned the ruff rule set in `pyproject.toml` (`[tool.ruff.lint] select`) and raised the dev
  floor to `ruff>=0.16`. Relying on ruff's default rule set made CI fail on an unrelated commit
  the day 0.16 shipped and enabled `I`/`UP`/`ISC`/`C4` by default. Import blocks sorted and the
  new findings fixed across the package, including files untouched by this release.

### Notes

- The output JSON contract is unchanged, so a 1.0.x payload still applies via `--input-json`
  provided its paths fall inside a track root.

[1.1.0]: https://github.com/nikolareljin/claude-docsmith/compare/1.0.1...1.1.0

---

## [1.0.1] - 2026-05-27

### Fixed

- `docs/publishing.md`: corrected marketplace source (`nikolareljin/claude-plugins`), slash-command syntax, version bump count (four → three), stale `commands/update-docs.md` reference, and old CLI-style troubleshooting commands
- `docs/publishing.md`: removed manual tagging step (step 7) — superseded by `release-tag` CI workflow
- `.github/workflows/release-tag.yml`: added `release-tag` workflow to auto-tag releases on merge to `main`

[1.0.1]: https://github.com/nikolareljin/claude-docsmith/compare/1.0.0...1.0.1

---

## [1.0.0] - 2026-05-27

### ⚠ BREAKING CHANGES

- **Claude Code command renamed**: `/update-docs` → `/nr-update-docs`

  Users who invoke the command directly must update their workflows. The standalone CLI
  (`claude-docsmith`) and all skill files are unchanged.

### Changed

- Claude Code command file renamed from `commands/update-docs.md` to `commands/nr-update-docs.md`
- Command now has a proper frontmatter header (`description`, `argument-hint`)
- Marketplace registry moved from `claude-docsmith` repo to dedicated `nikolareljin/claude-plugins`
- `plugin.json` no longer declares explicit `commands`/`skills` paths (auto-discovered from root)

### Migration

```
# Old
/update-docs

# New
/nr-update-docs
```

---

## [0.2.0] - 2026-04-21

### Added

- **Claude API provider** — httpx-based, reads `ANTHROPIC_API_KEY`; retry on 429/503/529
- **Ollama provider** — migrated from urllib to httpx; retry on 429/503/529
- CLI flags: `--max-context-kb`, `--skip-tests`, `--skip-checklists`, `--provider claude`
- `--dry-run` prints context stats: file count, KB, estimated tokens, detected language
- Language detection from manifest files (pyproject.toml, package.json, go.mod, Cargo.toml, etc.)
- `detected_language` and `total_bytes` fields on `RepoSnapshot`
- Compact JSON contract header in prompts; detected language included in prompt body
- `pr-gate.yml` CI workflow
- CI migrated to `ci-helpers` python.yml preset
- `vendor/script-helpers` git submodule (production branch, dev only)
- `ABOUT.md` with author attribution
- `docs/configuration.md` — full CLI flag reference, Ollama and Claude API setup
- `docs/demo.md` — step-by-step walkthrough
- `docs/developer-guide.md` — submodule init, linting, CI, release process
- Tests expanded to 16: scanner (language detection, byte budget, skip-tests, ignored dirs), `test_prompting.py`, `test_cli.py`

### Changed

- Scanner: expanded `SOURCE_DIR_NAMES`, `CONFIG_CANDIDATES`, `IGNORED_DIRS`
- Scanner enforces `max-context-kb` byte budget
- `pyproject.toml` bumped to 0.2.0; added `httpx` and `ruff` dependencies
- README updated to link configuration, demo, and About docs

### Fixed

- Provider defaults and float division errors
- Path traversal prefix check
- Sorted rglob restored for determinism; `response.json()` wrapped as `ProviderError`
- Scanner traversal edge cases and path base normalization
- Packaged skills and scanner safety guards
- Claude empty response handling
- Provider and scanner guard hardening
- Scanner budget handling edge cases
- Claude content parsing refinements

---

## [0.1.0] - 2026-04-09

Initial release.

### Added

- Plugin scaffold: `update-docs` skill, Claude Code command wiring (`commands/update-docs.md`)
- Official Claude plugin manifest at `.claude-plugin/plugin.json`
- Python CLI that scans a repository and prepares a prompt pack for documentation generation
- Prompt pack includes key docs, build metadata, source context, and the skill definition
- Optional Claude API or local Ollama call to write docs back to the target repo
- Generates user documentation and developer documentation
- `CONTRIBUTING.md`, `LICENSE` (MIT), `PRIVACY.md`, `SECURITY.md`, `TERMS.md`
- `docs/architecture.md`, `docs/developer-guide.md`
- GitHub Actions CI workflow
- `.gitignore`, `pyproject.toml`
- Claude marketplace install instructions and publishing notes in README and `docs/publishing.md`
- Plugin manifest aligned with official Claude plugin schema

[1.0.0]: https://github.com/nikolareljin/claude-docsmith/compare/0.2.0...1.0.0
[0.2.0]: https://github.com/nikolareljin/claude-docsmith/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/nikolareljin/claude-docsmith/releases/tag/0.1.0
