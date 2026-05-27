# Publishing Guide

## Overview

`claude-docsmith` is distributed through the `nikolareljin/claude-plugins` GitHub-hosted marketplace registry. This repository contains the plugin itself; the registry catalog lives at [github.com/nikolareljin/claude-plugins](https://github.com/nikolareljin/claude-plugins).

Publishing a new version is a branch, bump, PR, merge, and tag cycle.

## Files that matter

| File | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin manifest — version shown to Claude Code |
| `commands/nr-update-docs.md` | Claude Code slash command entrypoint (`/nr-update-docs`) |
| `skills/update-docs/SKILL.md` | Core skill behavior |
| `pyproject.toml` | Python package version |
| `src/claude_docsmith/__init__.py` | Python runtime version |

## How users install

Add the marketplace (one time, any Claude Code session):

```
/plugin marketplace add nikolareljin/claude-plugins
```

This registers the marketplace under the identifier `nikolareljin-plugins`.

Install the plugin:

```
/plugin install claude-docsmith@nikolareljin-plugins
```

Or interactively:

```text
/plugin
```

1. Choose `Browse Plugins`.
2. Add `nikolareljin/claude-plugins` as a marketplace if not present.
3. Select and install `claude-docsmith`.

After a plugin update, users refresh with:

```
/plugin marketplace update nikolareljin-plugins
/plugin update claude-docsmith@nikolareljin-plugins
```

## Maintainer release workflow

1. Create a release branch:

```bash
git checkout -b release/X.Y.Z
```

2. Bump the version in all three places:
   - `src/claude_docsmith/__init__.py`
   - `pyproject.toml`
   - `.claude-plugin/plugin.json`

3. Update `CHANGELOG.md` if present.

4. Validate the plugin manifest locally:

```bash
claude plugin validate .
```

5. Test the plugin locally:

```bash
claude --plugin-dir .
```

Inside Claude Code:

```text
/nr-update-docs
```

6. Commit, push the branch, and open a PR against `main`:

```bash
git push -u origin release/X.Y.Z
gh pr create --base main
```

7. After the PR merges, the `release-tag` CI workflow automatically creates and pushes the `X.Y.Z` tag from the merged release branch name. No manual tagging is needed.

## Submit to Anthropic's official plugin directory

Your GitHub-hosted marketplace handles self-distribution. Anthropic also documents a separate path for inclusion in the official `claude-plugins-official` directory.

Submission endpoints:

- `https://claude.ai/settings/plugins/submit`
- `https://platform.claude.com/plugins/submit`

You can submit either a GitHub repository link or a zip file. For this repository, submit:

```
https://github.com/nikolareljin/claude-docsmith
```

Notes:

- The official directory appears in Claude Code as `claude-plugins-official`.
- Submissions undergo automated review.
- Plugins may later receive an `Anthropic Verified` badge.
- Every update requires a new submission.

## Local development

Do not install from the marketplace during development. Use:

```bash
claude --plugin-dir .
```

Reload changes without restarting:

```text
/reload-plugins
```

## Troubleshooting

### Marketplace validates but install does not update

```
/plugin marketplace update nikolareljin-plugins
/plugin update claude-docsmith@nikolareljin-plugins
```

### Local changes are not visible

Run `/reload-plugins` inside Claude Code, or restart with `claude --plugin-dir .`.

### The command does not appear

Check that `.claude-plugin/plugin.json` and `commands/nr-update-docs.md` both exist and are valid.
