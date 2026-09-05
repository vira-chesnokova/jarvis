# Changelog

All notable changes to Jarvis are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [semver](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-09-05

First public release.

### Added
- Tab sweeping via AppleScript — reads every open tab from an already-running browser.
- Classification into three buckets: `project`, `watch`, `learning`.
- Live dashboard on `localhost` with resume, park, move, archive and inline notes.
- `profile.md` — persistent context about the user, read before every sweep.
- Append-only Corrections log that outranks the agent's own judgment.
- Evidence-first onboarding: detect, draft, correct — never a blank page.
- Support for Chrome, Chrome Beta/Canary, Chromium, Brave, Edge, Arc and Vivaldi.
- Codex port sharing the same scripts.

### Safety
- Every tab is written to `jarvis.json` before anything is closed.
- The browser is only ever addressed if already running; Jarvis never launches one.
- `protect` patterns are enforced in code, not by agent judgment.
- Atomic writes to the data store.
