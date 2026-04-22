# Contributing

## Development setup

```bash
git clone --recurse-submodules https://github.com/nikolareljin/claude-docsmith.git
cd claude-docsmith
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Validation

```bash
ruff check src tests
pytest
python3 -m compileall src
claude-docsmith . --dry-run
```

## Scope rules

- Keep the `update-docs` skill as the behavior source of truth.
- Do not invent repository features in generated docs.
- Prefer updating existing docs in target repositories over creating duplicates.
- Keep provider code small; avoid adding new runtime dependencies without discussion.

## Pull requests

- Explain any scanner heuristics you change.
- Include sample output or prompt changes when behavior changes materially.
- Keep changes focused on documentation generation, prompt quality, or packaging.
- Run the full validation suite before opening a PR.
