# Claude Docsmith

`claude-docsmith` is a Claude Code plugin for repository documentation, with a small optional helper CLI for prompt-pack generation and local Ollama fallback.

It packages an `update-docs` skill, Claude Code command wiring, and a small Python tool that scans a repository and prepares repository context for Claude Code. If you want a fully local fallback, the CLI can also send the same prompt pack to Ollama.

- plain user documentation
- developer documentation

The intended workflow is simple:

1. Point `claude-docsmith` at a repository.
2. Let it inspect docs, config, commands, source, and tests.
3. Generate a structured documentation plan or write updated docs into the target repo.

Public repository target: `https://github.com/nikolareljin/claude-docsmith`

## Why this name

`claude-docsmith` is short, searchable, and accurate:

- `claude` anchors the primary agent workflow
- `docsmith` says the tool forges and refreshes documentation from code

It also still fits if you use Ollama locally for generation.

## What is included

- A reusable `update-docs` skill under [`skills/update-docs`](./skills/update-docs)
- A Claude Code command under [`commands/update-docs.md`](./commands/update-docs.md)
- An official Claude plugin manifest under [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json)
- A Python CLI that:
  - scans the target repository
  - reads key docs and build metadata
  - builds a prompt pack from the codebase plus the skill definition
  - prints that prompt pack for Claude Code
  - optionally calls local Ollama
  - optionally writes model-produced documentation files back to the target repo

## Installation

Installation is only required if you want the CLI helper. The plugin itself follows the official Claude Code plugin layout and can be loaded directly by Claude Code.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Prerequisites

- Python 3.10+
- Claude Code for the primary workflow
- Optional Ollama fallback:
  - a local Ollama server running, typically at `http://127.0.0.1:11434`
  - a model already pulled locally

## Quick start

Test the plugin locally with Claude Code:

```bash
claude --plugin-dir ./claude-docsmith
```

Then invoke the namespaced command:

```text
/claude-docsmith:update-docs
```

During development, after changing the manifest, commands, or skills, reload them without restarting Claude Code:

```text
/reload-plugins
```

## Install In Claude

This repository is now both:

- the plugin source repo
- a GitHub-hosted Claude marketplace repo

Add the marketplace from GitHub:

```bash
claude plugin marketplace add nikolareljin/claude-docsmith
```

Install the plugin from that marketplace:

```bash
claude plugin install claude-docsmith@nikolareljin-plugins
```

Useful variants:

```bash
claude plugin install claude-docsmith@nikolareljin-plugins --scope user
claude plugin install claude-docsmith@nikolareljin-plugins --scope project
claude plugin install claude-docsmith@nikolareljin-plugins --scope local
```

Inside an interactive Claude Code session, the equivalent commands are:

```text
/plugin marketplace add nikolareljin/claude-docsmith
/plugin install claude-docsmith@nikolareljin-plugins
```

After installation, invoke the command with:

```text
/claude-docsmith:update-docs
```

Build the prompt pack for Claude Code with the helper CLI:

```bash
claude-docsmith /path/to/repo --dry-run
```

Then use that prompt in Claude Code with the bundled `update-docs` skill.

If you want a fully local fallback, generate with Ollama:

```bash
claude-docsmith /path/to/repo \
  --provider ollama \
  --model llama3.1 \
  --output-json docsmith-output.json
```

Apply a JSON result that came back from Claude Code or Ollama:

```bash
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

## Common usage

Use Claude Code plus the bundled skill as the default execution path.

Use the CLI when you want deterministic repository scanning, saved prompt packs, optional Ollama execution, or JSON apply support.

The plugin namespace comes from the `name` field in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json), so the command is intentionally namespaced as `/claude-docsmith:update-docs`.

Recommended pattern:

1. Run `claude-docsmith --dry-run` to inspect what context will be sent.
2. Send that prompt to Claude Code with the `update-docs` skill, or run Ollama locally.
3. Review the proposed file set.
4. Re-run with `--input-json ... --apply` once the file targets look correct.

## Output format

The model is instructed to return JSON like this:

```json
{
  "summary": "High-level documentation changes",
  "files": [
    {
      "path": "README.md",
      "audience": "user",
      "action": "update",
      "content": "# Updated README..."
    }
  ],
  "open_questions": [
    "Deployment workflow is still inferred from CI only."
  ],
  "follow_up_docs": [
    "docs/architecture.md"
  ]
}
```

## Repository layout

```text
claude-docsmith/
├── .claude-plugin/plugin.json
├── commands/update-docs.md
├── skills/update-docs/
├── src/claude_docsmith/
└── tests/
```

## Claude plugin conformance

This repository follows the official Claude Code plugin pattern:

- plugin manifest at `.claude-plugin/plugin.json`
- root-level `commands/` for namespaced slash commands
- root-level `skills/` for model-invoked skills
- local testing through `claude --plugin-dir ./claude-docsmith`
- explicit manifest component paths use schema-compliant `./`-relative plugin-root paths

Reference: [Create plugins](https://code.claude.com/docs/en/plugins)

The manifest also aligns with the published schema categories from the plugin reference:

- required field: `name`
- metadata fields: `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`
- component path fields: `commands`, `skills`

Reference: [Plugin manifest schema](https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema)

This repository also includes a marketplace catalog at [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json), following Anthropic’s marketplace guidance for GitHub-hosted distribution.

Reference: [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)

## Publish To Claude

Based on Anthropic’s current docs, “publishing” means hosting a plugin marketplace and letting users add that marketplace to Claude Code. GitHub is the recommended hosting method.

This repository is already set up for that flow:

1. Push plugin changes to `main` in `nikolareljin/claude-docsmith`.
2. Keep the plugin manifest in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json).
3. Keep the marketplace catalog in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).
4. Validate before sharing:

```bash
claude plugin validate .
```

5. Users add the marketplace:

```bash
claude plugin marketplace add nikolareljin/claude-docsmith
```

6. Users install the plugin:

```bash
claude plugin install claude-docsmith@nikolareljin-plugins
```

7. After you publish updates, users refresh with:

```bash
claude plugin marketplace update nikolareljin-plugins
claude plugin update claude-docsmith@nikolareljin-plugins
```

## What “publish” means here

- There is no separate deployment artifact required for this GitHub flow.
- The published unit is your GitHub repository plus `.claude-plugin/marketplace.json`.
- Users install through a marketplace, not by pointing Claude directly at `plugin.json`.
- For local development, keep using `claude --plugin-dir ./claude-docsmith`.

## Troubleshooting

### The model returns invalid JSON

Start with `--dry-run` and inspect the prompt pack. If the prompt is too large, lower `--max-files` or `--max-bytes-per-file`.

### Ollama requests fail

Confirm the daemon is running:

```bash
curl http://127.0.0.1:11434/api/tags
```

### The wrong docs are being targeted

Use the generated JSON review step before `--apply`. The tool prefers existing docs, but final file choice is still model-driven.

## FAQ

### Does this edit code?

No. It only generates or updates documentation files.

### Can I use only the skill without the CLI?

Yes. The plugin works through Claude Code directly; the CLI is optional.

### Does this support private repositories?

Yes, when run locally against a checked-out repo.

### Does it require Claude?

Claude Code is the primary path. Ollama is an optional local fallback.

## Security

- No credentials are stored in this repository.
- Generated artifacts such as `docsmith-output.json` and `docsmith-preview.md` are ignored by git.
- The CLI refuses to write outside the selected target repository.

## Developer notes

See [docs/developer-guide.md](./docs/developer-guide.md) and [docs/architecture.md](./docs/architecture.md).
