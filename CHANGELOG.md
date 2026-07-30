# Changelog

All notable changes to claude-docsmith are documented here.

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
