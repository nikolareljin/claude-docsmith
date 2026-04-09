# Contributing

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Validation

```bash
pytest
python3 -m compileall src
env PYTHONPATH=src python3 -m claude_docsmith.cli . --dry-run
```

## Scope rules

- Keep the `update-docs` skill as the behavior source of truth.
- Do not invent repository features in generated docs.
- Prefer updating existing docs in target repositories over creating duplicates.
- Keep provider code small and dependency-light.

## Pull requests

- Explain any scanner heuristics you change.
- Include sample output or prompt changes when behavior changes materially.
- Keep changes focused on documentation generation, prompt quality, or packaging.
