# User Documentation Checklist

Verify every item before declaring the user track complete.

## Coverage

- [ ] What the project does, in one sentence
- [ ] Who it is for, and who it is not for
- [ ] `index.md` lists every user-visible capability, each linking to its feature page
- [ ] Prerequisites stated before installation
- [ ] Installation steps, one path per supported platform
- [ ] First run, and what success looks like
- [ ] A first real task completed end to end
- [ ] One feature page per user-visible feature, screen, or command
- [ ] Every option, setting, field, and flag documented with purpose, default, and when to change it
- [ ] Troubleshooting: symptom, cause, fix, with error messages quoted exactly
- [ ] FAQ answering questions the code can actually answer
- [ ] Upgrade or migration notes when behavior changed

## Screenshots

- [ ] Existing repository images reviewed before requesting new captures
- [ ] Capture target and shot list approved before accessing a device or window
- [ ] Key states use real, inspected captures rather than mockups
- [ ] Every screenshot referenced with a stable kebab-case id
- [ ] Alt text describes what the image shows
- [ ] No broken image links
- [ ] `screenshots/manifest.yml` is sorted by id and records every present or missing shot
- [ ] Missing shots use visible callouts with reproducible steps and a concrete blocker
- [ ] No screenshot contains credentials, personal data, device ids, or account details

## Tone

- [ ] No module paths, class names, or type signatures
- [ ] No code blocks except text the reader types verbatim
- [ ] Technical terms defined on first use
- [ ] No "simply", "just", or "obviously"

## Safety

- [ ] No credential, token, key, or connection string appears anywhere
- [ ] No `[REDACTED:...]` marker reproduced in the output
