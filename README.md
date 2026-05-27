# Claude Docsmith

`claude-docsmith` is a Claude Code plugin for repository documentation, with an optional CLI for prompt-pack generation and local Ollama or Claude API fallback.

It packages an `update-docs` skill, Claude Code command wiring, and a Python tool that scans a repository and prepares context for documentation generation. The plugin generates:

- plain user documentation
- developer documentation

The intended workflow:

1. Point `claude-docsmith` at a repository.
2. Let it inspect docs, config, commands, source, and tests.
3. Generate a structured documentation plan or write updated docs into the target repo.

## What is included

- A reusable `update-docs` skill under [`skills/update-docs`](./skills/update-docs)
- A Claude Code command under [`commands/nr-update-docs.md`](./commands/nr-update-docs.md)
- An official Claude plugin manifest under [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json)
- A Python CLI that:
  - scans the target repository
  - reads key docs and build metadata
  - builds a prompt pack from the codebase plus the skill definition
  - prints that prompt pack for Claude Code
  - optionally calls the Claude API or local Ollama
  - optionally writes model-produced documentation files back to the target repo

---

## Install as Claude Code Plugin

**Step 1 — Add the marketplace** (one time, any Claude Code session):

```
/plugin marketplace add nikolareljin/claude-plugins
```

**Step 2 — Install the plugin:**

```
/plugin install claude-docsmith@claude-plugins
```

**Step 3 — Restart Claude Code**, then run:

```
/nr-update-docs
```

### Install scopes

```
/plugin install claude-docsmith@claude-plugins --scope user     # all projects (default)
/plugin install claude-docsmith@claude-plugins --scope project  # this project only
/plugin install claude-docsmith@claude-plugins --scope local    # local only, not committed
```

### Verify installation

```
/plugin
```

The plugin should appear under `claude-plugins`. If the command does not appear after restart, run `/reload-plugins`.

---

## Install the CLI (optional)

The CLI is optional. Install it only if you want the prompt-pack generator or direct provider integration.

**Prerequisites**: Python 3.10+

**Linux / WSL (Ubuntu/Debian)**

```bash
# Option A: pipx (recommended — isolated, no system conflicts)
pipx install claude-docsmith

# Option B: user install
pip install --user claude-docsmith
```

> **pipx not installed?** `sudo apt install pipx` (Ubuntu 23.04+) or `pip install --user pipx`

**macOS**

```bash
brew install pipx
pipx install claude-docsmith
```

**From source**

```bash
git clone https://github.com/nikolareljin/claude-docsmith
cd claude-docsmith
pipx install -e "."
```

Verify:

```bash
claude-docsmith --help
```

---

## Quick start

### Plugin (Claude Code)

```bash
cd /path/to/your-project
claude
```

Then:

```
/nr-update-docs
```

### CLI with Claude API

```bash
export ANTHROPIC_API_KEY=sk-ant-...

claude-docsmith /path/to/repo \
  --provider claude \
  --model claude-opus-4-6 \
  --output-json docsmith-output.json

claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

### CLI with local Ollama

```bash
claude-docsmith /path/to/repo \
  --provider ollama \
  --model llama3.1 \
  --output-json docsmith-output.json

claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

### Inspect the prompt without calling a model

```bash
claude-docsmith /path/to/repo --dry-run
```

This prints the assembled prompt and a context stats footer showing file count, total KB, estimated token count, and detected language.

---

## Common usage

Use Claude Code plus the bundled skill as the default path.

Use the CLI when you want deterministic repository scanning, saved prompt packs, direct provider integration, or JSON apply support.

Recommended pattern:

1. Run `--dry-run` to inspect what context will be sent.
2. Generate with `--provider claude` or `--provider ollama`.
3. Review the proposed file set in the output JSON.
4. Apply with `--input-json ... --apply` once the file targets look correct.

---

## Output format

The model returns JSON:

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

---

## Repository layout

```text
claude-docsmith/
├── .claude-plugin/plugin.json      plugin manifest
├── commands/nr-update-docs.md      Claude Code slash command (/nr-update-docs)
├── skills/update-docs/             skill definition and checklists
├── src/claude_docsmith/            CLI source
└── tests/                          unit tests
```

---

## Troubleshooting

### The model returns invalid JSON

Use `--dry-run` to inspect the prompt. If the prompt is too large, lower `--max-files`, `--max-bytes-per-file`, or `--max-context-kb`. Add `--skip-tests` or `--skip-checklists` to reduce further.

### Claude API requests fail

Confirm `ANTHROPIC_API_KEY` is set and valid.

### Ollama requests fail

Confirm the daemon is running:

```bash
curl http://127.0.0.1:11434/api/tags
```

### The wrong docs are being targeted

Review the output JSON before using `--apply`. The tool prefers existing docs, but final file choice is model-driven.

---

## FAQ

### Does this edit code?

No. It only generates or updates documentation files.

### Can I use only the skill without the CLI?

Yes. The plugin works through Claude Code directly; the CLI is optional.

### Does this support private repositories?

Yes, when run locally against a checked-out repo.

### Does it require a network connection?

Only when using `--provider claude` (requires `ANTHROPIC_API_KEY`) or when Claude Code processes the prompt. Use `--provider ollama` with a local Ollama server for a fully offline workflow.

---

## Security

No credentials are stored in this repository. Runtime secrets (`ANTHROPIC_API_KEY`) are expected through environment variables only. The CLI refuses to write outside the selected target repository.

See [SECURITY.md](./SECURITY.md) for the vulnerability reporting policy.

---

## Configuration

Full flag reference, Ollama setup, and Claude API setup: [docs/configuration.md](./docs/configuration.md)

## Demo

Step-by-step walkthrough and screenshot guide: [docs/demo.md](./docs/demo.md)

## Publishing

Maintainer publish workflow and Anthropic official directory submission: [docs/publishing.md](./docs/publishing.md)

## Developer notes

See [docs/developer-guide.md](./docs/developer-guide.md) and [docs/architecture.md](./docs/architecture.md).

## About

Built and maintained by [Nikola Reljin](https://github.com/nikolareljin).
See [ABOUT.md](./ABOUT.md) for contact and contribution links.
