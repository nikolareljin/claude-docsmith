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

Users can also install interactively through the Claude plugin UI:

```text
/plugin
```

Then:

1. choose `Browse Plugins`
2. add `nikolareljin/claude-docsmith` as a marketplace if it is not already present
3. select `claude-docsmith`
4. install it from the `nikolareljin-plugins` marketplace

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

## Submit to Anthropic's official plugin directory

Your own GitHub-hosted marketplace is enough for self-distribution and team/community use, but Anthropic also documents a separate submission path for inclusion in the official directory.

Anthropic’s documented submission endpoints are:

- `https://claude.ai/settings/plugins/submit`
- `https://platform.claude.com/plugins/submit`

Anthropic says you can submit either:

- a GitHub repository link
- or a zip file containing the plugin and its folder structure

For this repository, the preferred submission target is:

- `https://github.com/nikolareljin/claude-docsmith`

Notes from Anthropic’s docs:

- the official directory appears in Claude Code as `claude-plugins-official`
- plugin submissions undergo automated review
- plugins may later receive an `Anthropic Verified` badge after additional review
- every plugin update requires a new submission

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
- Inclusion in Anthropic’s official directory is separate from your own marketplace and requires submission through Anthropic’s form.

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
