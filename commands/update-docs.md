Use the bundled `update-docs` skill from this plugin to refresh both user-facing and developer-facing documentation.

Goals:
- inspect the repository before editing docs
- verify commands and APIs against code and config
- update both plain-user and developer documentation
- prefer updating existing docs over creating duplicates

Recommended flow:

1. Run `/claude-docsmith:update-docs` inside Claude Code when this plugin is loaded.
2. Let Claude inspect the target repository and apply the `skills/update-docs/SKILL.md` workflow.
3. Optionally use the local helper CLI only for prompt-pack generation or Ollama fallback:

```bash
claude-docsmith . --dry-run
claude-docsmith . --provider ollama --model llama3.1 --output-json docsmith-output.json
claude-docsmith . --input-json docsmith-output.json --apply
```

Authoritative workflow files:

- `skills/update-docs/SKILL.md`
- `skills/update-docs/templates/user-doc-checklist.md`
- `skills/update-docs/templates/developer-doc-checklist.md`
