# Developer Guide

## Local setup

```bash
git clone --recurse-submodules https://github.com/nikolareljin/claude-docsmith.git
cd claude-docsmith
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

## Submodules

`vendor/script-helpers` (pinned to the `production` branch) is vendored for local development tooling only. It is not bundled into the Claude plugin and is not required by plugin users.

## Commands

Run tests and lint:

```bash
pytest
ruff check src tests
python -m compileall src
```

Run the CLI:

```bash
claude-docsmith /path/to/repo --dry-run
```

Test the Claude plugin locally:

```bash
claude --plugin-dir .
```

Then inside Claude Code:

```text
/claude-docsmith:update-docs
/reload-plugins
```

Install from the public GitHub marketplace repo:

```bash
claude plugin marketplace add nikolareljin/claude-docsmith
claude plugin install claude-docsmith@nikolareljin-plugins
```

See [`docs/publishing.md`](./publishing.md) for the full publish and update workflow.

Build a source distribution:

```bash
python3 -m build
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required when using `--provider claude` |
| `OLLAMA_BASE_URL` | Override Ollama server URL. Default: `http://127.0.0.1:11434` |

Full configuration reference: [`docs/configuration.md`](./configuration.md)

## Project structure

```
claude-docsmith/
├── .claude-plugin/plugin.json      official Claude Code plugin manifest
├── .claude-plugin/marketplace.json GitHub-hosted marketplace catalog
├── .github/workflows/ci.yml        CI via ci-helpers python preset
├── .github/workflows/pr-gate.yml   PR gate via ci-helpers pr-gate preset
├── commands/update-docs.md         namespaced Claude command entrypoint
├── docs/                           developer docs
├── skills/update-docs/             skill definition and checklists
├── src/claude_docsmith/
│   ├── cli.py                      CLI entrypoint and apply flow
│   ├── scanner.py                  repository scanning and file selection
│   ├── prompting.py                prompt assembly
│   ├── providers.py                Ollama and Claude API adapters
│   └── models.py                   dataclasses and JSON parsing
├── tests/                          unit tests
└── vendor/script-helpers/          dev tooling submodule (not in plugin)
```

## CI

CI uses reusable workflows pinned to `nikolareljin/ci-helpers@0.7.2`:

- **ci.yml**: runs on push and pull request. Runs lint (`ruff`) and tests (`pytest` + `compileall`).
- **pr-gate.yml**: runs on pull request. Adds release tag validation for `release/X.Y.Z` branches.

## Contribution workflow

1. Branch off `main` or create a `release/X.Y.Z` branch for a new version.
2. Update scanner, prompt logic, or providers.
3. Add or adjust unit tests.
4. Run `pytest` and `ruff check src tests`.
5. Smoke-test the CLI with `--dry-run`.
6. Test the plugin with `claude --plugin-dir .`.
7. Use `/reload-plugins` after plugin file changes.
8. Validate manifest: `claude plugin validate .`.
9. Open a PR against `main`.

## Release process

1. Create release branch: `git checkout -b release/X.Y.Z`
2. Bump version in:
   - `src/claude_docsmith/__init__.py`
   - `pyproject.toml`
   - `.claude-plugin/plugin.json`
   - `.claude-plugin/marketplace.json`
3. Update `CHANGELOG.md`.
4. Push branch and open PR against `main`.
5. After merge, tag `main`: `git tag X.Y.Z && git push origin X.Y.Z`.
6. Users update with: `claude plugin update claude-docsmith@nikolareljin-plugins`.

## Debugging tips

- Use `--dry-run` to inspect the prompt and context stats without network calls.
- Use `--output-json` to save the raw structured result before applying.
- If generation quality drops, inspect `skills/update-docs/SKILL.md` — it drives behavior more than the Python code.
- If the prompt is too large, use `--skip-tests`, `--skip-checklists`, or lower `--max-context-kb`.
