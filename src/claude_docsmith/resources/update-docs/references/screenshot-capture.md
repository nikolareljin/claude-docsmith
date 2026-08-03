# Screenshot Capture Reference

Use screenshots only when they materially help a reader recognise a screen,
complete a pivotal action, confirm a result, or recover from an important error.
Prefer a small set of useful states over an image for every numbered step.

## Discover and plan

1. Inspect existing images under `docs/`, `assets/`, `screenshots/`, `.github/`,
   `static/`, and `public/`. Reuse a suitable current image before capturing a
   replacement. Match by stable id, filename, directory, and the feature page.
2. Read an existing `docs/user/screenshots/manifest.yml` before changing it.
   Preserve hand-edited captions, alt text, steps, and ids when they remain true.
3. Build a short shot list containing the entry state, pivotal action or result,
   and an important error state only when each one adds information.
4. Inventory the available browser, device, emulator, simulator, CLI, and desktop
   capture targets without changing them.
5. Show the proposed target and shot list to the user. Obtain explicit approval
   before connecting to a physical device or capturing any device, window, or
   desktop content.

## Choose the capture tool

Use the first suitable tool already available locally:

1. **Browser interface:** Playwright. Use a deterministic viewport, wait for the
   documented state rather than a fixed delay, and capture the relevant page or
   element.
2. **Android interface:** ADB with an approved device or emulator, using a PNG
   screencap. Prefer an emulator when no physical device was approved.
3. **Apple interface:** for a simulator, use the locally installed Apple tooling
   and its simulator screenshot command. Use a physical device only when it was
   explicitly approved and the installed debugging tooling supports capture. Do
   not guess an unsupported command; use a simulator or record a blocker.
4. **CLI or terminal interface:** use an installed CLI/TUI screenshot utility
   supplied by the project or environment. Capture the actual rendered command
   and output, not a reconstructed transcript.
5. **Desktop interface:** use the operating system's window or region screenshot
   tool. Capture only the application window or relevant region; avoid the full
   desktop when a narrower capture communicates the same information.

Do not install capture tools, alter device settings, unlock or reset a device,
accept a trust prompt, or start an emulator download without separate approval.
Use repository-provided start and test commands when they exist.

## Inspect and store

- Use controlled demo data. Before adding a file, inspect the image at readable
  resolution for credentials, personal information, account details, device ids,
  notifications, unrelated windows, and incorrect or stale state.
- If sensitive content is visible, remove it from the running application and
  recapture. Do not publish a blurred or masked secret-bearing original.
- Save PNG captures as `docs/user/screenshots/<id>.png`, where `<id>` is stable,
  descriptive kebab-case. Do not manufacture, illustrate, or substitute a mockup
  for a capture described as real.
- Reference a present image with descriptive alt text that says what the reader
  can identify or verify in it.

## Capture manifest

Maintain `docs/user/screenshots/manifest.yml` as a YAML list sorted by `id`.
Every desired shot appears exactly once.

Present capture:

```yaml
- id: dashboard-ready
  status: present
  page: features/dashboard.md
  caption: Dashboard after the first successful import
  alt: Dashboard showing the completed import and three available reports
  steps:
    - Start the application with demo data
    - Complete the first import
  file: screenshots/dashboard-ready.png
```

Missing capture:

```yaml
- id: dashboard-ready
  status: missing
  page: features/dashboard.md
  caption: Dashboard after the first successful import
  alt: Dashboard showing the completed import and three available reports
  steps:
    - Start the application with demo data
    - Complete the first import
  blocker: No supported browser or approved device is available
```

For a missing entry, place a visible callout on the page containing the caption
and blocker. Never emit an image link to a missing file. If local execution,
capture, or image inspection is unavailable, continue the documentation update,
record the blocker, and never claim that a screenshot was captured.
