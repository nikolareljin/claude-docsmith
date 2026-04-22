---
name: update-docs
description: Update project documentation for both plain users and developers based on the current codebase, configuration, commands, APIs, and recent changes.
---

# Update Docs Skill

Use this skill when:
- features, commands, APIs, config, setup steps, or workflows change
- README or docs may be stale
- a user asks to update documentation
- code changes need both user-facing and developer-facing documentation

## Goals

Maintain two distinct documentation tracks:

1. Plain user documentation
   - installation - only if the tool requires installation
   - quick start
   - common usage
   - examples
   - troubleshooting
   - FAQ
   - upgrade notes when relevant

2. Developer documentation
   - local setup
   - architecture
   - build/test/lint commands
   - environment variables
   - API contracts
   - internal workflows
   - contribution guidance
   - deployment notes where appropriate

## Required behavior

- Inspect the repository before editing docs.
- Read existing documentation first.
- Prefer updating existing docs over creating duplicates.
- Do not invent features, commands, or behavior.
- If behavior is unclear, infer only from code, config, tests, scripts, and existing docs.
- Keep user documentation non-technical where possible.
- Keep developer documentation precise and implementation-oriented.
- Preserve concise structure and headings.
- Include examples where useful.
- When commands are documented, verify them against package scripts, Makefiles, Docker files, CI config, or source code.
- When APIs are documented, verify against actual routes, handlers, schemas, or tests.

## Suggested file targets

Prioritize these when present:

### User-facing

- README.md
- docs/user-guide.md
- docs/getting-started.md
- docs/installation.md
- docs/troubleshooting.md
- docs/faq.md

### Developer-facing

- docs/developer-guide.md
- docs/architecture.md
- docs/api.md
- docs/contributing.md
- CLAUDE.md, AGENTS.md, COPILOT.md

## Workflow

1. Read:
   - README.md
   - docs/**
   - CLAUDE.md
   - package.json / pyproject.toml / go.mod / Cargo.toml / Makefile / Dockerfile / CI files
   - source files relevant to changed behavior
   - tests relevant to changed behavior

2. Identify:
   - what changed
   - which docs are stale
   - whether the change affects users, developers, or both

3. Update user docs:
   - installation/setup
   - usage steps
   - examples
   - troubleshooting
   - limitations if relevant

4. Update developer docs:
   - architecture or module notes
   - setup/build/test instructions
   - APIs/interfaces
   - environment/config details
   - contribution or workflow guidance

5. Summarize:
   - Which files were updated
   - what changed
   - any remaining undocumented ambiguity

## Output format

At the end, provide:
- Updated files
- Key doc changes
- Open questions or uncertainties
- Suggested follow-up docs to add later

## Quality bar

The documentation is complete only if:
- plain users can install and use the project without reading source code
- developers can set up, run, test, and modify the project without guesswork
- commands and APIs match the actual implementation
- stale or conflicting wording is removed

## Templates

Read these checklists when drafting or validating output:

- `templates/user-doc-checklist.md`
- `templates/developer-doc-checklist.md`
