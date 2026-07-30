# Developer Reference

The reader is an engineer who will read the code, call it, extend it, or operate
it. Precision beats brevity. Anything a reader would otherwise have to confirm by
opening the source is missing information.

## Page set

All paths are relative to the developer track root (`docs/developer/`).

### `index.md`

- What the codebase is, in engineering terms.
- Repository layout: each top-level directory and what lives there.
- Where to start reading for the three most common tasks.
- Local setup, build, test, and lint commands, verified against the build
  manifest and CI config — not guessed.

### `architecture.md`

- Components and their responsibilities.
- Data flow, end to end, following one real request or invocation.
- Boundaries: what the system deliberately does not do.
- Design decisions and their trade-offs, where the code makes them evident.
- Environment variables: name, purpose, default, required or optional. Never a
  value.

### `api/index.md`

Every API surface the project exposes, grouped by version. State how a caller
selects a version (URL prefix, header, query parameter) and which versions are
current, deprecated, or removed. Link to the per-version pages.

If the project exposes no network API, say so explicitly and document the public
programmatic interface instead. Do not invent an HTTP surface.

### `api/<version>/<resource>.md`

One page per resource per API version. Do not merge versions onto one page — a
caller pinned to v1 must be able to read only v1.

Each endpoint documents:

- Method and full path, including path parameters.
- What it does, in one sentence.
- Authentication and authorization required.
- Path parameters, query parameters, and request body fields, as a table with
  name, type, required, default, and constraints.
- Response shape with field types.
- Every status code the handler can return, with what causes it.
- A worked request and its response.
- Version differences: what changed from the previous version of this resource.

### `reference/modules.md` and `reference/classes.md`

Public functions and classes, grouped by module. Each entry carries:

- Full signature, including parameter names, type annotations, and defaults.
- Return type.
- What it does and any side effects.
- Errors or exceptions raised, and when.
- For classes: base classes, public attributes, public methods with full
  signatures, and whether the class is intended for subclassing.

Private helpers (leading underscore, non-exported) are documented only when a
reader must understand them to use the public surface.

### `extending.md`

- Extension points, listed explicitly.
- Which classes are designed to be subclassed and which methods to override.
- Which protocols or interfaces to implement, with their required members.
- A worked example: a small, complete, runnable subclass or implementation.
- What is deliberately not extensible, and why.

## Writing rules

- Signatures must match the source exactly. Copy them; do not paraphrase.
- State versions, defaults, and required flags. "Optional" without a default is
  incomplete.
- Every command must be copy-pasteable and verified against the build manifest,
  Makefile, Dockerfile, or CI workflow.
- Document what the code does, not what it should do. Known gaps go in an open
  questions list, not into prose as if implemented.
- Never document a credential value. Name the environment variable and describe
  how an operator supplies it.

## Completeness bar

The developer track is done when an engineer can set up the project, run its
tests, call every public endpoint with correct parameters for the version they
target, understand every public class and function signature without opening the
source, and extend the system through documented extension points.
