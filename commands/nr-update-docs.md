---
description: Refresh user-facing and developer-facing documentation for the current repository
argument-hint: "[--audience user|developer|both] [--dry-run]"
---

Use the bundled `update-docs` skill from this plugin to refresh both user-facing and developer-facing documentation.

Goals:
- inspect the repository before editing docs
- verify commands and APIs against code and config
- update both documentation tracks, one at a time:
  - the user manual under `docs/user/`
  - the developer reference under `docs/developer/`
- prefer updating existing docs over creating duplicates
- never copy a credential into documentation, and never reproduce a `[REDACTED:...]` marker

Recommended flow:

1. Run `/nr-update-docs` inside Claude Code when this plugin is loaded.
2. Let Claude inspect the target repository and apply the `skills/update-docs/SKILL.md` workflow.
3. Optionally use the local helper CLI only for prompt-pack generation or Ollama fallback:

```bash
claude-docsmith . --dry-run                       # one prompt per track
claude-docsmith . --dry-run --audience developer  # developer track only
claude-docsmith . --provider ollama --output-json docsmith-output.json   # model auto-detected
claude-docsmith . --input-json docsmith-output.json --apply
claude-docsmith . --check                         # offline freshness gate
```

Authoritative workflow files:

- `skills/update-docs/SKILL.md`
- `skills/update-docs/references/user-manual.md`
- `skills/update-docs/references/developer-reference.md`
- `skills/update-docs/templates/user-doc-checklist.md`
- `skills/update-docs/templates/developer-doc-checklist.md`
- `skills/update-docs/templates/pages/`
