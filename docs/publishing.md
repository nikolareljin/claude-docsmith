# Publishing Guide

## Overview

`claude-docsmith` is published to Claude Code through a GitHub-hosted marketplace.

This repository contains both:

- the plugin itself
- the marketplace catalog at `.claude-plugin/marketplace.json`

That means publishing a new plugin version is mostly a Git push plus validation.

## Files that matter

- `.claude-plugin/plugin.json`: plugin manifest
- `.claude-plugin/marketplace.json`: marketplace catalog
- `commands/update-docs.md`: namespaced Claude command
- `skills/update-docs/SKILL.md`: core skill behavior

## How users install it

Users add the marketplace:

```bash
claude plugin marketplace add nikolareljin/claude-docsmith
```

Then install the plugin:

```bash
claude plugin install claude-docsmith@nikolareljin-plugins
```

## Maintainer publish workflow

1. Make plugin changes.
2. Update `version` in `.claude-plugin/plugin.json` when you want a visible release bump.
3. Validate the marketplace and plugin metadata:

```bash
claude plugin validate .
```

4. Test locally:

```bash
claude --plugin-dir ./claude-docsmith
```

5. Inside Claude Code, confirm the plugin loads:

```text
/claude-docsmith:update-docs
```

6. Commit and push to `main`:

```bash
git push origin main
```

7. Users refresh their local marketplace and plugin copies:

```bash
claude plugin marketplace update nikolareljin-plugins
claude plugin update claude-docsmith@nikolareljin-plugins
```

## Local development

For development, do not install from the marketplace repeatedly. Use:

```bash
claude --plugin-dir ./claude-docsmith
```

Then reload changes inside Claude Code with:

```text
/reload-plugins
```

## Important notes

- Users install through the marketplace, not by targeting `plugin.json` directly.
- The marketplace name is `nikolareljin-plugins`.
- The plugin install id is `claude-docsmith@nikolareljin-plugins`.
- This repository uses a GitHub plugin source in the marketplace entry, which is appropriate for GitHub-hosted distribution.

## Troubleshooting

### Marketplace validates but install does not update

Run:

```bash
claude plugin marketplace update nikolareljin-plugins
claude plugin update claude-docsmith@nikolareljin-plugins
```

### Local changes are not visible during testing

Use:

```text
/reload-plugins
```

or restart Claude Code with:

```bash
claude --plugin-dir ./claude-docsmith
```

### The command does not show up

Check that the plugin manifest exists at `.claude-plugin/plugin.json` and that the command file exists at `commands/update-docs.md`.
