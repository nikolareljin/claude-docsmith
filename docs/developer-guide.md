# Developer Guide

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Commands

Run the CLI:

```bash
claude-docsmith /path/to/repo --dry-run
```

Run tests:

```bash
pytest
```

Build a source distribution:

```bash
python3 -m build
```

## Environment variables

- `ANTHROPIC_API_KEY`: required for `--provider anthropic`
- `OLLAMA_BASE_URL`: optional override, defaults to `http://127.0.0.1:11434`

## Project structure

- `src/claude_docsmith/cli.py`: CLI entrypoint and apply flow
- `src/claude_docsmith/scanner.py`: repository scanning and file selection
- `src/claude_docsmith/prompting.py`: prompt assembly and JSON instructions
- `src/claude_docsmith/providers.py`: Anthropic and Ollama HTTP adapters
- `src/claude_docsmith/models.py`: shared dataclasses and JSON parsing
- `skills/update-docs/`: reusable documentation skill and checklists
- `.claude/commands/update-docs.md`: Claude Code command wrapper
- `.codex-plugin/plugin.json`: plugin metadata for marketplaces and cross-agent packaging

## Contribution workflow

1. Update scanner or prompt logic.
2. Add or adjust unit tests.
3. Run `pytest`.
4. Smoke-test the CLI with `--dry-run`.
5. Validate one real repository using either Anthropic or Ollama.

## Debugging tips

- Use `--dry-run` to inspect the prompt pack without network calls.
- Use `--output-json` to save the raw structured result before applying changes.
- If generation quality drops, inspect `skills/update-docs/SKILL.md` first. That file intentionally drives behavior more than the Python code does.

## CI/CD notes

No CI workflow is included yet. Recommended next step is a simple GitHub Actions pipeline running:

```bash
pip install -e .
pytest
python3 -m compileall src
```
