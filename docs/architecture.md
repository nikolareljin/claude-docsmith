# Architecture

`claude-docsmith` is intentionally small. The skill defines the documentation policy; the Python package provides repeatable context gathering plus an optional Ollama fallback.

## Flow

1. The CLI receives a target repository path and provider settings.
2. The scanner inspects common docs, config files, scripts, CI files, source trees, and tests.
3. The prompt builder embeds:
   - the `update-docs` skill
   - both documentation checklists
   - a compact repository inventory
   - excerpts from relevant files
4. Claude Code uses that prompt plus the bundled skill to generate structured JSON, or the optional Ollama adapter does it locally.
5. The response parser expects structured JSON with file targets and contents.
6. The apply step writes documentation files only when `--apply` is set.

For Claude Code plugin usage, the plugin manifest in `.claude-plugin/plugin.json` identifies the plugin, while Claude Code loads the root-level `commands/` and `skills/` directories using the standard plugin directory layout.

## Design choices

- Standard library only: keeps installation simple.
- JSON output contract: easier to review and safer to apply than free-form prose.
- Read-first scanning: the model gets docs and code context together, so it can remove stale wording instead of only adding new text.
- Existing-doc preference: prompt instructions tell the model to update current docs before creating new files.
- Claude-first execution: the repository does not depend on direct Anthropic API calls or an `ANTHROPIC_API_KEY`.

## Boundaries

- The tool does not mutate source code.
- It does not run project-specific build or test commands in the target repository.
- It does not infer undocumented behavior beyond code, config, tests, and existing docs.

## Future extensions

- Diff-aware updates against git history
- Per-language scanners with richer command extraction
- Multi-turn repair when the first model response is not valid JSON
- Built-in GitHub Action wrapper
