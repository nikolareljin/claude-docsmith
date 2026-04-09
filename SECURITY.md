# Security Policy

## Supported versions

Security fixes are applied to the latest `main` branch state.

## Reporting a vulnerability

Do not open a public issue for security reports.

Use GitHub private vulnerability reporting for this repository once it is enabled.

Until then, report privately through a non-public channel you control.

## Security notes

- This repository contains no bundled credentials.
- Runtime secrets are expected through local environment variables only.
- The CLI writes only inside the selected target repository and rejects path traversal outside it.
