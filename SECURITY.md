# Security Policy

## Supported versions

Security fixes are applied to the latest release on `main`.

## Reporting a vulnerability

Do not open a public GitHub issue for security reports.

Use [GitHub private vulnerability reporting](https://github.com/nikolareljin/claude-docsmith/security/advisories/new) for this repository, or contact via [GitHub](https://github.com/nikolareljin) directly.

## Security notes

- This repository contains no bundled credentials.
- Runtime secrets (`ANTHROPIC_API_KEY`) are expected through local environment variables only.
- The CLI writes only inside the selected target repository and rejects path traversal outside it.
