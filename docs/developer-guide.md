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
claude-docsmith /path/to/repo --dry-run                  # one prompt per track
claude-docsmith /path/to/repo --dry-run --audience user  # single track
claude-docsmith /path/to/repo --check                    # offline freshness gate
```

Test the Claude plugin locally:

```bash
claude --plugin-dir .
```

Then inside Claude Code:

```text
/claude-docsmith:nr-update-docs
/reload-plugins
```

Install from the public GitHub marketplace repo:

```
/plugin marketplace add nikolareljin/claude-plugins
/plugin install claude-docsmith@nikolareljin-plugins
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
| `DOCSMITH_CLAUDE_MODEL` | Model for `--provider claude` when `--model` is not given |
| `DOCSMITH_OLLAMA_MODEL` | Model for `--provider ollama` when `--model` is not given |
| `DOCSMITH_MODEL` | Model for any provider; lower precedence than the per-provider variables |

`tests/test_providers.py::test_no_model_identifier_is_hardcoded` fails the build if a
model name is ever pinned in `src/claude_docsmith/*.py`. Resolution order lives in
`cli._resolve_model`; discovery lives in `providers.discover_model`.

Full configuration reference: [`docs/configuration.md`](./configuration.md)

## Project structure

```
claude-docsmith/
├── .claude-plugin/plugin.json      official Claude Code plugin manifest
├── .github/workflows/ci.yml        CI via ci-helpers python preset
├── .github/workflows/pr-gate.yml   PR gate via ci-helpers pr-gate preset
├── commands/nr-update-docs.md      namespaced Claude command entrypoint
├── docs/                           developer docs
├── skills/update-docs/
│   ├── SKILL.md                    orchestrator; routes to one reference per track
│   ├── references/                 per-audience specs (user manual, developer reference)
│   └── templates/                  checklists and page skeletons
├── src/claude_docsmith/
│   ├── cli.py                      CLI entrypoint, track loop, apply flow, drift gate
│   ├── audiences.py                the two tracks: roots, references, path allowlists
│   ├── scanner.py                  repository scanning, deny list, inbound redaction
│   ├── redaction.py                sensitive-path deny list and credential scrubbing
│   ├── prompting.py                per-track prompt assembly
│   ├── manifest.py                 docs manifest, source hashing, drift detection
│   ├── providers.py                Ollama and Claude API adapters
│   └── models.py                   dataclasses and JSON parsing
├── tests/                          unit tests
└── vendor/script-helpers/          dev tooling submodule (not in plugin)
```

## CI

CI uses reusable workflows from `nikolareljin/ci-helpers@production`:

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
3. Update `CHANGELOG.md`.
4. Push branch and open PR against `main`.
5. After merge, the `release-tag` CI workflow automatically creates and pushes the `X.Y.Z` tag.
6. Users update with: `/plugin update claude-docsmith@nikolareljin-plugins`.

## Editing the skill

`skills/update-docs/` is mirrored byte-for-byte into
`src/claude_docsmith/resources/update-docs/` so the packaged wheel carries the same
files the plugin loads. `tests/test_resources.py` fails if the two diverge, so after
editing the skill:

```bash
rm -rf src/claude_docsmith/resources/update-docs
cp -r skills/update-docs src/claude_docsmith/resources/update-docs
pytest tests/test_resources.py
```

New file types also need a glob in `[tool.setuptools.package-data]` in `pyproject.toml`,
or they are silently missing from the wheel.

## Debugging tips

- Use `--dry-run` to inspect each track's prompt and context stats without network calls.
- Use `--output-json` to save the raw structured result before applying.
- If generation quality drops, inspect the track's reference under
  `skills/update-docs/references/` — those drive behavior more than the Python code.
- If the prompt is too large, use `--skip-tests`, `--skip-checklists`, `--audience` to
  generate one track at a time, or lower `--max-context-kb`.
- `--fail-on-secret` prints `path:line kind` for every credential-shaped match without ever
  printing the value; use it to audit a repository before pointing a provider at it.
