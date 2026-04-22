# Privacy Policy

`claude-docsmith` does not collect telemetry.

What data leaves your machine depends on the configured provider:

- **Claude Code plugin** (`/claude-docsmith:update-docs`): repository excerpts are processed through your Claude Code session.
- **`--provider claude`**: repository excerpts are sent to the Anthropic API. Your `ANTHROPIC_API_KEY` is used for authentication. Anthropic's data handling policies apply.
- **`--provider ollama`**: prompts stay local if your Ollama server is local. No data leaves your machine.

You are responsible for reviewing repository contents before sending them to a remote model provider.
