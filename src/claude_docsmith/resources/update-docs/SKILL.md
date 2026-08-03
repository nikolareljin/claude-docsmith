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

## Two tracks, generated separately

This skill produces **two independent documentation trees**. Work one track at a
time and finish it before starting the other. They have different readers,
different vocabulary, and different completeness bars.

| Track | Reader | Output root | Detailed spec |
|---|---|---|---|
| User manual | Non-technical person using the product | `docs/user/` | `references/user-manual.md`, then `references/screenshot-capture.md` |
| Developer reference | Engineer reading, extending, or calling the code | `docs/developer/` | `references/developer-reference.md` |

Read the reference for the track you are writing. Read the matching checklist in
`templates/` before declaring the track done. Page skeletons live in
`templates/pages/`.

Never mix tracks in one page. If a user page needs an implementation detail to
make sense, link to the developer page instead of explaining it inline.

## Required behavior

- Inspect the repository before editing docs.
- Read existing documentation first.
- Prefer updating existing docs over creating duplicates.
- Do not invent features, commands, behavior, endpoints, or parameters.
- Infer only from code, config, tests, scripts, and existing docs.
- Verify commands against package scripts, Makefiles, Dockerfiles, CI config, or source.
- Verify APIs against actual routes, handlers, schemas, or tests.
- Preserve concise structure and headings.
- Remove stale or contradicting wording rather than leaving it beside new text.

## Security

- Never copy a credential, token, key, password, or connection string into documentation.
- Content may arrive with `[REDACTED:kind]` markers. Never reproduce a marker and never
  guess what it replaced. Document the setting by name and explain how a reader supplies
  their own value.
- Some files are deliberately not read (`.env`, private keys, credential stores). Do not
  ask for them and do not describe their contents.

## Workflow

1. Read: `README.md`, `docs/**`, `CLAUDE.md`, the build manifest
   (`package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `Makefile` /
   `Dockerfile` / CI files), source relevant to changed behavior, and the tests
   that pin that behavior.

2. Identify: what changed, which pages are stale, and whether the change affects
   the user track, the developer track, or both.

3. Write the user track against `references/user-manual.md`.

   When the project has a graphical, browser, mobile, desktop, or terminal
   interface, also follow `references/screenshot-capture.md`. Capture requires
   approval of the target and shot list before accessing a device or window.

4. Write the developer track against `references/developer-reference.md`.

5. Summarize: files updated, what changed, remaining ambiguity.

## Output format

At the end, provide:
- Updated files, grouped by track
- Key doc changes
- Open questions or uncertainties
- Suggested follow-up docs to add later

## Quality bar

Documentation is complete only when:
- a non-technical reader can install and use the project without opening source
- every user-visible option is documented with what it does and when to change it
- a developer can set up, run, test, and extend the project without guesswork
- every public endpoint, class, and function signature matches the implementation
- commands are copy-pasteable and verified against the repository

## Templates

- `references/user-manual.md`
- `references/developer-reference.md`
- `templates/user-doc-checklist.md`
- `templates/developer-doc-checklist.md`
- `templates/pages/user-index.md`
- `templates/pages/user-feature.md`
- `templates/pages/api-endpoint.md`
- `templates/pages/class-reference.md`
