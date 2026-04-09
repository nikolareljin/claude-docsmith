# /update-docs

Use the bundled `update-docs` skill from this repository.

Goal:
- inspect the repository first
- verify commands and APIs against code and config
- update both user-facing and developer-facing docs
- prefer updating existing documentation over creating duplicates

Suggested local helper flow:

```bash
claude-docsmith . --dry-run
claude-docsmith . --provider anthropic --model claude-sonnet-4-5 --output-json docsmith-output.json
```

The authoritative instructions for the workflow live in:

- `skills/update-docs/SKILL.md`
- `skills/update-docs/templates/user-doc-checklist.md`
- `skills/update-docs/templates/developer-doc-checklist.md`
