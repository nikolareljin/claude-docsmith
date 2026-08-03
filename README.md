<div align="center">

<!-- Absolute URL and PNG on purpose: this file is also the PyPI long description,
     which cannot resolve relative paths and does not render SVG.
     Vector source: assets/logo-hero.svg -->
<img src="https://raw.githubusercontent.com/nikolareljin/claude-docsmith/main/assets/logo-hero.png"
     alt="Claude Docsmith — user and developer documentation, forged from your code."
     width="820">

<!-- Not PyPI badges: this package is not published there, so shields.io renders
     "package or version not found". Version comes from the git tag the release
     workflow creates; the Python badge shows the requires-python floor. -->
[![Release](https://img.shields.io/github/v/tag/nikolareljin/claude-docsmith?color=F97316&label=release&sort=semver)](https://github.com/nikolareljin/claude-docsmith/tags)
[![Python](https://img.shields.io/badge/python-3.10%2B-F97316)](https://github.com/nikolareljin/claude-docsmith/blob/main/pyproject.toml)
[![CI](https://github.com/nikolareljin/claude-docsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/nikolareljin/claude-docsmith/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-F97316)](./LICENSE)
[![Docs](https://img.shields.io/badge/docs-github%20pages-F97316)](https://nikolareljin.github.io/claude-docsmith/)

</div>

`claude-docsmith` is a Claude Code plugin for repository documentation, with an optional CLI for prompt-pack generation and local Ollama or Claude API fallback.

It packages an `update-docs` skill, Claude Code command wiring, and a Python tool that scans a repository and prepares context for documentation generation. It generates **two independent documentation tracks**, each with its own prompt, its own provider call, and its own output tree:

- `docs/user/` — a plain-language manual for non-technical readers
- `docs/developer/` — an engineering reference covering APIs (including versioned endpoints), classes, function signatures, and extension points

The intended workflow:

1. Point `claude-docsmith` at a repository.
2. Let it inspect docs, config, commands, source, and tests.
3. Generate a structured documentation plan or write updated docs into the target repo.

## What is included

- A reusable `update-docs` skill under [`skills/update-docs`](./skills/update-docs)
- Screenshot-aware user documentation that discovers existing images and can use
  approved local browser, mobile, CLI, or desktop capture tools when the application
  is available
- A Claude Code command under [`commands/nr-update-docs.md`](./commands/nr-update-docs.md)
- An official Claude plugin manifest under [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json)
- A Python CLI that:
  - scans the target repository
  - reads key docs and build metadata
  - builds a prompt pack from the codebase plus the skill definition
  - prints that prompt pack for Claude Code
  - optionally calls the Claude API or local Ollama
  - optionally writes model-produced documentation files back to the target repo
  - scrubs credential-shaped content before it reaches a provider
  - records what was generated, and from which sources, in `docs/.docsmith/manifest.json`

---

## Install as Claude Code Plugin

**Step 1 — Add the marketplace** (one time, any Claude Code session):

```
/plugin marketplace add nikolareljin/claude-plugins
```

**Step 2 — Install the plugin:**

```
/plugin install claude-docsmith@nikolareljin-plugins
```

**Step 3 — Restart Claude Code**, then run:

```
/claude-docsmith:nr-update-docs
```

### Install scopes

```
/plugin install claude-docsmith@nikolareljin-plugins --scope user     # all projects (default)
/plugin install claude-docsmith@nikolareljin-plugins --scope project  # this project only
/plugin install claude-docsmith@nikolareljin-plugins --scope local    # local only, not committed
```

### Verify installation

```
/plugin
```

The plugin should appear under `nikolareljin-plugins`. If the command does not appear after restart, run `/reload-plugins`.

---

## Install the CLI (optional)

The CLI is optional. Install it only if you want the prompt-pack generator or direct provider integration.

**Prerequisites**: Python 3.10 or newer. CI tests 3.10, 3.11 and 3.12.

The package is not on PyPI yet, so install it from the repository.

**Linux / WSL / macOS**

```bash
# Option A: pipx (recommended — isolated, no system conflicts)
pipx install git+https://github.com/nikolareljin/claude-docsmith.git

# Option B: user install
pip install --user git+https://github.com/nikolareljin/claude-docsmith.git
```

> **pipx not installed?** `sudo apt install pipx` (Ubuntu 23.04+), `brew install pipx` (macOS),
> or `pip install --user pipx`.

Pin a released version by appending a tag:

```bash
pipx install git+https://github.com/nikolareljin/claude-docsmith.git@1.3.0
```

**From source (for development)**

```bash
git clone --recurse-submodules https://github.com/nikolareljin/claude-docsmith
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
/claude-docsmith:nr-update-docs
```

### CLI with Claude API

```bash
export ANTHROPIC_API_KEY=sk-ant-...

claude-docsmith /path/to/repo \
  --provider claude \
  --output-json docsmith-output.json

claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

### CLI with local Ollama

```bash
claude-docsmith /path/to/repo \
  --provider ollama \
  --output-json docsmith-output.json

claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

### Choosing a model

No model name is baked into the tool. With no `--model`, it asks the provider what is
available — the most recently modified installed Ollama model, or the newest model your
Anthropic key can see — and prints what it picked:

```
Using ollama model: qwen2.5:14b
```

Override in order of precedence: `--model <name>`, then `DOCSMITH_CLAUDE_MODEL` /
`DOCSMITH_OLLAMA_MODEL`, then `DOCSMITH_MODEL`. Pin one when you want reproducible
output across runs.

### Inspect the prompt without calling a model

```bash
claude-docsmith /path/to/repo --dry-run
```

This prints one prompt per track, each under an `=== AUDIENCE: <track> ===` separator, with a context stats footer showing file count, total KB, estimated token count, and detected language.

### Generate a single track

```bash
claude-docsmith /path/to/repo --audience user       # user manual only
claude-docsmith /path/to/repo --audience developer  # developer reference only
```

### Check whether the docs still match the code

```bash
claude-docsmith /path/to/repo --check
```

Exits `0` when the documentation is current and `1` when sources have moved since it
was generated. Runs entirely offline — no API key, no network — so it is safe as a CI gate.

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
      "path": "docs/user/getting-started.md",
      "audience": "user",
      "action": "update",
      "content": "# Getting started..."
    },
    {
      "path": "docs/developer/api/v1/orders.md",
      "audience": "developer",
      "action": "create",
      "content": "# GET /api/v1/orders..."
    }
  ],
  "open_questions": [
    "Deployment workflow is still inferred from CI only."
  ],
  "follow_up_docs": [
    "docs/developer/architecture.md"
  ]
}
```

Each track is generated by its own provider call, and the results are merged into
this single payload. Files may only be written inside their own track's root
(`docs/user/**` or `docs/developer/**`); the user track may additionally write
`README.md`. Anything else is rejected.

---

## Generated documentation layout

```text
docs/
  user/                     non-technical manual
    index.md  getting-started.md
    features/<slug>.md
    screenshots/
      manifest.yml          stable list of present and missing shots
    troubleshooting.md  faq.md
  developer/                engineering reference
    index.md  architecture.md
    api/index.md  api/<version>/<resource>.md
    reference/{modules,classes}.md
    extending.md
  .docsmith/manifest.json   generated-file index plus source hashes
```

The manifest is what makes `--check` possible and is the ingestion point for
publishing the docs elsewhere.

### Screenshots in the user manual

The user track inventories existing PNG, JPEG, GIF, WebP, and SVG assets without
reading their binary content into the prompt. Suitable current images are reused.
When local capture is available, the skill proposes a target and a short list of
key states, then waits for approval before accessing a device or window.

Capture selection follows the interface:

- Playwright for browser pages
- ADB for approved Android devices and emulators
- installed Apple debugging tools for supported simulators or approved devices
- an installed CLI/TUI screenshot utility for terminal interfaces
- the operating system's window or region tool for desktop applications

Real captures are stored under `docs/user/screenshots/` and tracked in
`docs/user/screenshots/manifest.yml`. Each entry has a stable id, page, caption,
alt text, reproduction steps, and either a file or an actionable blocker. Missing
shots appear as visible callouts rather than broken image links. Every capture is
inspected, and screens containing credentials or personal information are
recaptured with controlled demo data before use.


---

## Repository layout
```text
claude-docsmith/
├── .claude-plugin/plugin.json      plugin manifest
├── assets/                         logo sources (SVG) and rendered PNGs
├── site/                           GitHub Pages landing page
├── commands/nr-update-docs.md      Claude Code slash command (/claude-docsmith:nr-update-docs)
├── skills/update-docs/             skill definition, per-audience references, checklists, page templates
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

Confirm the daemon is running and has at least one model pulled:

```bash
curl http://127.0.0.1:11434/api/tags
ollama list
```

With no models installed the tool exits 1 rather than guessing a name.

### The wrong docs are being targeted

Review the output JSON before using `--apply`. The tool prefers existing docs, and a
generated file is rejected outright if it falls outside its track's root.

### `--check` reports drift immediately after generating

The check compares the current sources against the hashes recorded when the docs were
written. Editing code after generation is drift by design — regenerate and commit both.

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

No credentials are stored in this repository. Runtime secrets (`ANTHROPIC_API_KEY`) are expected through environment variables only. The CLI refuses to write outside the selected target repository, and outside the track a file belongs to.

Before any repository content reaches a model provider:

- Files matching a sensitive-name deny list are never opened — `.env` and `.env.*`
  (except `.env.example` / `.env.sample` / `.env.template`), private keys, keystores,
  `.netrc`, `.npmrc`, `.pypirc`, credential stores, and Terraform state.
- Credential-shaped values in files that *are* read are replaced with a
  `[REDACTED:<kind>]` marker.

The same scrub runs on model output before `--apply` writes. Findings record
`path`, `line`, and `kind` only — never the value. Use `--fail-on-secret` to exit `2`
instead of continuing, and `--no-redact` to opt out of content scrubbing (the
file deny list still applies).

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

## Documentation site

[nikolareljin.github.io/claude-docsmith](https://nikolareljin.github.io/claude-docsmith/) —
install, plugin usage, and a worked standalone run against Ollama. The page lives in
[`site/`](./site) and deploys from `main` via `.github/workflows/pages.yml`.

## Logo

The mark is a document on an anvil under a forge spark: source code struck into
documentation. Vector sources and rendered PNGs live in [`assets/`](./assets).

| File | Use |
|---|---|
| `assets/logo.svg` | Square mark, 512×512. Canonical source |
| `assets/logo.png` | Square mark, rasterized for contexts without SVG support |
| `assets/logo-hero.svg` | Wide banner with wordmark, 1200×320. Canonical source |
| `assets/logo-hero.png` | Banner used by this README and on PyPI |

Regenerate the derived files after editing either SVG:

```bash
inkscape assets/logo.svg      -o assets/logo.png      -w 512  -h 512
inkscape assets/logo-hero.svg -o assets/logo-hero.png -w 1200 -h 320
python3 scripts/render_site_mark.py   # site/logo-mark.svg, used by the docs site
```

`tests/test_site.py` fails if `site/logo-mark.svg` drifts from `assets/logo.svg`.

## About

Built and maintained by [Nikola Reljin](https://github.com/nikolareljin).
See [ABOUT.md](./ABOUT.md) for contact and contribution links.
