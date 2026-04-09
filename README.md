# Claude Docsmith

`claude-docsmith` is a GitHub-ready repository for a documentation-focused Claude Code plugin and helper CLI.

It packages an `update-docs` skill, Claude Code command wiring, and a small Python tool that scans a repository and asks either Anthropic Claude or a local Ollama model to produce two documentation tracks:

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
- A Claude Code command under [`.claude/commands/update-docs.md`](./.claude/commands/update-docs.md)
- A Codex-style plugin manifest under [`.codex-plugin/plugin.json`](./.codex-plugin/plugin.json)
- A Python CLI that:
  - scans the target repository
  - reads key docs and build metadata
  - builds a prompt pack from the codebase plus the skill definition
  - calls either Anthropic Claude or local Ollama
  - emits structured file updates
  - optionally writes those files back to the target repo

## Installation

Installation is only required if you want the CLI helper. The skill files can be copied into Claude Code directly without installing Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Prerequisites

- Python 3.10+
- For Anthropic mode:
  - `ANTHROPIC_API_KEY`
- For Ollama mode:
  - a local Ollama server running, typically at `http://127.0.0.1:11434`
  - a model already pulled locally

## Quick start

Preview the prompt pack without calling a model:

```bash
claude-docsmith /path/to/repo --dry-run
```

Generate documentation suggestions with Claude:

```bash
export ANTHROPIC_API_KEY=your_key
claude-docsmith /path/to/repo \
  --provider anthropic \
  --model claude-sonnet-4-5 \
  --output-json docsmith-output.json
```

Generate with Ollama:

```bash
claude-docsmith /path/to/repo \
  --provider ollama \
  --model llama3.1 \
  --output-json docsmith-output.json
```

Apply generated files into the target repository:

```bash
claude-docsmith /path/to/repo \
  --provider ollama \
  --model llama3.1 \
  --apply
```

## Common usage

Use the CLI when you want deterministic repository scanning and a reusable automation entrypoint.

Use the skill by itself when Claude Code is already editing the repository and only needs a disciplined documentation workflow.

Recommended pattern:

1. Run `claude-docsmith --dry-run` to inspect what context will be sent.
2. Generate JSON output.
3. Review the proposed file set.
4. Re-run with `--apply` once the file targets look correct.

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
├── .claude/commands/update-docs.md
├── .codex-plugin/plugin.json
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

### Anthropic requests fail

Check that `ANTHROPIC_API_KEY` is set and that the selected model is enabled for your account.

### The wrong docs are being targeted

Use the generated JSON review step before `--apply`. The tool prefers existing docs, but final file choice is still model-driven.

## FAQ

### Does this edit code?

No. It only generates or updates documentation files.

### Can I use only the skill without the CLI?

Yes. The skill and the Claude command wrapper are plain text assets.

### Does this support private repositories?

Yes, when run locally against a checked-out repo.

### Does it require Claude?

No. Anthropic Claude and local Ollama are both supported.

## Security

- No credentials are stored in this repository.
- `ANTHROPIC_API_KEY` is read from the local environment only at runtime.
- Generated artifacts such as `docsmith-output.json` and `docsmith-preview.md` are ignored by git.
- The CLI refuses to write outside the selected target repository.

## Developer notes

See [docs/developer-guide.md](./docs/developer-guide.md) and [docs/architecture.md](./docs/architecture.md).
