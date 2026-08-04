# User Manual Reference

The reader is a person using the product, not building it. They may never open a
terminal, never read source, and never have heard the project's internal
vocabulary. Everything they need to succeed must be on the page in front of them.

## Page set

All paths are relative to the user track root (`docs/user/`).

### `index.md`

- One sentence saying what the product does.
- Who it is for, and one line on who it is *not* for.
- "What you can do with it": a bulleted list of every user-visible capability,
  each linking to its feature page. This list is the table of contents a reader
  scans first, so it must be complete.
- Link to `getting-started.md` as the next step.

### `getting-started.md`

- Prerequisites, stated as things the reader must already have.
- Installation, one numbered path per supported platform. Do not interleave
  platforms in a single list.
- First run: the exact steps, and what a successful result looks like.
- First real task, completed end to end, so the reader finishes with a win.
- Where to go next.

### `features/<slug>.md`

One page per user-visible feature, screen, command, or workflow. Slugs are
kebab-case and stable — other pages and screenshot ids link to them.

Each page contains:

- What this feature is for, in one or two sentences.
- When you would use it, and when you would not.
- Numbered steps to use it, written as actions the reader takes.
- **Every** option, setting, field, or flag the feature exposes, as a table with:
  what it does, its default, and when to change it. A feature page is not
  complete while any user-visible option is undocumented.
- What happens next / what the result looks like.
- Related features.

### `troubleshooting.md`

One section per failure a reader can actually hit. Each section: the symptom as
the reader experiences it, the cause in plain language, and the fix as steps.
Quote error messages exactly — that is what the reader will search for.

### `faq.md`

Real questions a non-technical reader asks. Prefer questions answered by the code
(limits, costs, privacy, offline use, data handling) over invented ones.

### `screenshots/`

Reference images as `![clear description](screenshots/<id>.png)` with a stable
kebab-case id matching the feature. Alt text describes what the image shows, not
"screenshot". Follow `screenshot-capture.md` to reuse existing assets, capture
real application states when local tools are available, and maintain
`screenshots/manifest.yml` without broken image links.

## Writing rules

- Plain language. If a technical term is unavoidable, define it the first time it
  appears on that page.
- Second person: "you open", "you select".
- No module paths, class names, function names, or type signatures. Those belong
  to the developer track.
- No code blocks except text the reader types or pastes verbatim.
- One idea per sentence. Short paragraphs.
- Never write "simply", "just", or "obviously".
- Every claim must be traceable to code, config, tests, or existing docs. When
  behavior cannot be determined, leave it out and record it as an open question.
- Prefer a table when documenting three or more parallel items.

## Completeness bar

The user track is done when a reader who has never seen the source can install
the product, complete its main task, understand every option they can change,
and recover from the failures the code can actually produce.
