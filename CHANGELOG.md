# Changelog

All notable changes to claude-docsmith are documented here.

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

[0.2.0]: https://github.com/nikolareljin/claude-docsmith/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/nikolareljin/claude-docsmith/releases/tag/0.1.0
