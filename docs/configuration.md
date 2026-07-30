# Configuration Reference

## CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `target_repo` | positional | — | Path to the repository to document |
| `--provider` | `claude` \| `ollama` | none | AI provider to use for generation |
| `--model` | string | see below | Model name for the selected provider |
| `--audience` | `user` \| `developer` \| `both` | `both` | Which documentation track to generate. `both` makes one provider call per track |
| `--docs-dir` | string | `docs` | Documentation root inside the target repo |
| `--dry-run` | flag | off | Print the assembled prompt and context stats for each track; do not call a model |
| `--apply` | flag | off | Write generated documentation files into the target repository |
| `--check` | flag | off | Offline freshness check against the docs manifest. Exits 1 on drift, 0 when current. Makes no network request |
| `--output-json` | path | — | Save the structured model output to a JSON file |
| `--input-json` | path | — | Load a previously saved JSON result and optionally apply it |
| `--max-files` | int | 40 | Maximum number of files to include in the context |
| `--max-bytes-per-file` | int | 8000 | Maximum bytes to read from each file |
| `--max-context-kb` | int | 128 | Total context byte budget in KB; scanning stops when this limit is reached |
| `--skip-tests` | flag | off | Exclude test files from the context to save tokens |
| `--skip-checklists` | flag | off | Omit documentation checklists from the prompt to save tokens |
| `--no-redact` | flag | redaction on | Disable credential redaction. Sensitive files stay excluded regardless |
| `--fail-on-secret` | flag | off | Exit 2 when credential-shaped content is found. Values are never printed |
| `--timeout` | int | 300 | Request timeout in seconds |
| `--version` | flag | — | Print the installed version and exit |

### Default models

- `--provider claude`: `claude-opus-5`
- `--provider ollama`: `llama3.1`

Override with `--model <name>`.

---

## Environment variables

| Variable | Provider | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | `claude` | Anthropic API key. Required when using `--provider claude` |
| `OLLAMA_BASE_URL` | `ollama` | Ollama server base URL. Default: `http://127.0.0.1:11434` |

---

## Using with the Claude API

1. Obtain an API key from https://console.anthropic.com.

2. Export the key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

3. Run generation:

```bash
claude-docsmith /path/to/repo \
  --provider claude \
  --model claude-opus-5 \
  --output-json docsmith-output.json
```

4. Review the proposed file set, then apply:

```bash
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply

# 5. Later, check whether the docs still match the code
claude-docsmith /path/to/repo --check
```

---

## Output layout

`--apply` writes into two audience-scoped trees plus a machine-readable manifest:

```text
docs/
  user/                     non-technical manual
    index.md  getting-started.md
    features/<slug>.md
    screenshots/
    troubleshooting.md  faq.md
  developer/                engineering reference
    index.md  architecture.md
    api/index.md  api/<version>/<resource>.md
    reference/{modules,classes}.md
    extending.md
  .docsmith/manifest.json   generated-file index plus source hashes
```

A generated file is rejected unless it lands inside its own track's root. The user
track may also write `README.md`. Nothing else is writable.

---

## Redaction

Before any content reaches a provider:

- Files matching a sensitive-name deny list are never opened (`.env` and `.env.*`
  except the sample variants, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`,
  `*.keystore`, `*.kubeconfig`, `id_rsa*`, `id_ed25519*`, `.netrc`, `.npmrc`,
  `.pypirc`, `.htpasswd`, `credentials`, `*credentials*.json`, `secrets.*`,
  `terraform.tfstate*`).
- Credential-shaped values in files that *are* read are replaced with a
  `[REDACTED:<kind>]` marker.

Redaction runs again on model output before `--apply` writes, because the scanner
only reads a bounded file set and a model can echo a value it saw elsewhere.

Findings record `path`, `line`, and `kind` only — never the value.

**Model options**: `claude-opus-5` (best quality), `claude-sonnet-5` (faster, lower cost).

---

## Using with local Ollama

1. Install Ollama from https://ollama.com.

2. Pull a model:

```bash
ollama pull llama3.1
```

3. Verify the daemon is running:

```bash
curl http://127.0.0.1:11434/api/tags
```

4. Run generation:

```bash
claude-docsmith /path/to/repo \
  --provider ollama \
  --model llama3.1 \
  --output-json docsmith-output.json
```

5. Apply results:

```bash
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

**Larger models produce better output.** Recommended: `llama3.3:70b`, `qwen2.5:72b`. Expect longer inference times; increase `--timeout` accordingly (e.g., `--timeout 1800`).

**Custom server URL**:

```bash
export OLLAMA_BASE_URL=http://192.168.1.10:11434
```

---

## Token budget tuning

The `--dry-run` flag prints a stats footer:

```
--- context stats ---
files: 18  content: 42.3 KB  prompt: 51.2 KB  ~tokens: 13,107
detected language: python
```

If the prompt is too large or the model returns malformed JSON:

- Lower `--max-files` (e.g., `--max-files 20`)
- Lower `--max-bytes-per-file` (e.g., `--max-bytes-per-file 4000`)
- Lower `--max-context-kb` (e.g., `--max-context-kb 64`)
- Add `--skip-tests` to drop test files
- Add `--skip-checklists` to drop the built-in documentation checklists
- Generate one track at a time with `--audience user` / `--audience developer`

Each track is a separate provider call with its own output budget, so `--audience both`
sends roughly twice the context of 1.0.x but is not constrained to one shared response.

---

## Recommended workflow

```bash
# 1. Inspect what context will be sent (one prompt per track)
claude-docsmith /path/to/repo --dry-run

# 1b. Fail early if the repository contains credential-shaped content
claude-docsmith /path/to/repo --dry-run --fail-on-secret

# 2. Generate docs
claude-docsmith /path/to/repo \
  --provider claude \
  --output-json docsmith-output.json

# 3. Review the proposed file set
cat docsmith-output.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['summary'])
for f in d['files']:
    print(f['path'], f['action'])
"

# 4. Apply once satisfied
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```
