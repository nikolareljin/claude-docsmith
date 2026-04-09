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
