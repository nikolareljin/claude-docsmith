# Configuration Reference

## CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `target_repo` | positional | — | Path to the repository to document |
| `--provider` | `claude` \| `ollama` | none | AI provider to use for generation |
| `--model` | string | see below | Model name for the selected provider |
| `--dry-run` | flag | off | Print the assembled prompt and context stats; do not call a model |
| `--apply` | flag | off | Write generated documentation files into the target repository |
| `--output-json` | path | — | Save the structured model output to a JSON file |
| `--input-json` | path | — | Load a previously saved JSON result and optionally apply it |
| `--max-files` | int | 40 | Maximum number of files to include in the context |
| `--max-bytes-per-file` | int | 8000 | Maximum bytes to read from each file |
| `--max-context-kb` | int | 128 | Total context byte budget in KB; scanning stops when this limit is reached |
| `--skip-tests` | flag | off | Exclude test files from the context to save tokens |
| `--skip-checklists` | flag | off | Omit documentation checklists from the prompt to save tokens |
| `--timeout` | int | 180 | Request timeout in seconds |

### Default models

- `--provider claude`: `claude-opus-4-6`
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
  --model claude-opus-4-6 \
  --output-json docsmith-output.json
```

4. Review the proposed file set, then apply:

```bash
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

**Model options**: `claude-opus-4-6` (best quality), `claude-sonnet-4-6` (faster, lower cost).

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

---

## Recommended workflow

```bash
# 1. Inspect what context will be sent
claude-docsmith /path/to/repo --dry-run

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
