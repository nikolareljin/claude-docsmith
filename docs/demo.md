# Demo and Screenshots

This page walks through using `claude-docsmith` end-to-end. Screenshots show the experience inside Claude Code.

---

## Workflow A: Claude Code plugin (recommended)

### Step 1 — Install the plugin

```bash
claude plugin marketplace add nikolareljin/claude-docsmith
claude plugin install claude-docsmith@nikolareljin-plugins
```

![Plugin installation in terminal](screenshots/install.png)

### Step 2 — Open Claude Code in your target repository

```bash
cd /path/to/your-project
claude
```

### Step 3 — Invoke the skill

Type the command in the Claude Code session:

```
/claude-docsmith:update-docs
```

Claude reads your repository structure, existing docs, config files, and source and proposes updated documentation.

![Skill invocation and repo scan](screenshots/invoke.png)

### Step 4 — Review the proposed file set

Claude lists the files it plans to create or update, along with a summary of changes and any open questions.

![Proposed file review](screenshots/review.png)

### Step 5 — Confirm and apply

Approve the proposed changes. Claude writes the updated documentation files into your repository.

![Documentation written to repo](screenshots/result.png)

---

## Workflow B: CLI with Claude API

```bash
# Generate
claude-docsmith /path/to/repo \
  --provider claude \
  --model claude-opus-4-6 \
  --output-json docsmith-output.json

# Review
cat docsmith-output.json

# Apply
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

---

## Workflow C: CLI with local Ollama

```bash
# Start Ollama and pull a model
ollama pull llama3.1

# Generate
claude-docsmith /path/to/repo \
  --provider ollama \
  --model llama3.1 \
  --output-json docsmith-output.json

# Apply
claude-docsmith /path/to/repo \
  --input-json docsmith-output.json \
  --apply
```

---

## Adding screenshots

Screenshots should be captured manually from real Claude Code sessions.

Place them in `docs/screenshots/` as PNG files. Suggested filenames:

| File | What to show |
|------|-------------|
| `install.png` | Plugin install command output |
| `invoke.png` | `/claude-docsmith:update-docs` typed in Claude Code |
| `review.png` | Claude listing proposed doc files |
| `result.png` | Updated markdown file open in editor |

To record an animated demo, use a screen recorder and export as GIF or MP4.
Link it in `README.md` under Quick Start.
