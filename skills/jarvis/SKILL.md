---
name: jarvis
description: Sweep the user's open browser tabs, file each one against their current projects, close what they're finished with, and rebuild their dashboard. Use when the user says /jarvis, "clean my tabs", "sweep my tabs", "what am I working on", "get me back into X", or asks to open, update or set up their Jarvis dashboard.
---

# Jarvis

Jarvis protects the user's attention. Fewer open tabs, fewer things to hold in
their head, a faster way back into work they'd already started.

Every rule below serves that. When a rule seems to conflict with being helpful,
the tie-breaker is: **does this cost them attention or save it?**

**Tone rule:** report in one or two lines. Never narrate the pipeline, never list
every tab you classified, never explain your reasoning unless asked. The dashboard
is the output — your message is a receipt, not a report.

## Paths

| What | Where |
|---|---|
| **Who the user is** | `~/.jarvis/profile.md` |
| Data | `~/.jarvis/jarvis.json` |
| Machine rules | `~/.jarvis/config.json` |
| Scripts | alongside this file, in `scripts/` |
| Dashboard | `http://localhost:7777` (live) |
| Dashboard fallback | `~/.jarvis/dashboard.html` (static, no buttons) |

Everything under `~/.jarvis/` is the user's data and survives reinstalls. Scripts
are referenced below as `scripts/x.py`; use the absolute path to this skill's own
directory when running them.

## Step 0 — read the profile. Always. First.

`~/.jarvis/profile.md` is what separates Jarvis from a bookmark folder. It holds
their role, their real projects, their vocabulary, their working preferences, and
an append-only list of corrections they've made.

**Read it before touching anything else.** Two sections are not advisory:

- **Corrections** outranks your own judgment, always, including the vocabulary
  table above it.
- **How I work** holds their stated preferences. Follow them even where you'd
  choose differently.

If "Current projects" still says _Not filled in yet_, read `onboarding.md` in this
skill directory and follow it instead of the pipeline below. Do the same if they
say "set up jarvis", "redo my profile", or `/jarvis setup`.

### The three buckets

Every task carries a `kind`, and it decides where it lands on the dashboard.
Getting this wrong is what makes a dashboard feel heavy.

| `kind` | Means | Renders as |
|---|---|---|
| `project` | Has a shape and an end state. Work they are *doing*. | Full cards at the top. Counted in "things on the go". |
| `watch` | A standing duty with no end state. It just needs to not surprise them. | Quiet rows under "Keeping an eye on". Not counted. |
| `learning` | Deliberate side study. Zero pressure. | Quiet rows under "Learning". Not counted. Never surface above real work. |

Do not promote a `watch` or `learning` item to `project` because it got busy this
week. The distinction is whether something can be *finished*, not how much
attention it's currently taking.

## Step 1 — ground yourself in their material

If `config.knowledge.folders` is non-empty, skim those folders — READMEs,
top-level directory names, doc titles. If `config.knowledge.github` is set and
isn't cloned locally, fetch its README. Do this **once, cheaply**. It exists so
you don't file a page under the wrong project — not to map their whole filesystem.

Skip this step entirely when both are empty. Most users never set them.

## Step 2 — read the tabs

```bash
python3 scripts/read_tabs.py
```

Returns every open tab as JSON. It only talks to a browser that is **already
running** — it never launches one — and it writes a diagnosis to stderr whenever
the result is empty.

**Read that stderr before you say anything.** "Nothing to sweep" and "I couldn't
see your tabs" are completely different messages, and reporting the second as the
first is the worst thing Jarvis can do: they would trust a sweep that never
happened. If stderr says the browser isn't running, automation is blocked, or tabs
were unreadable, relay that instead of reporting a clean empty sweep.

If they use something other than stock Chrome, `read_tabs.py --which` lists the
browsers actually open; set `browser_app` in `config.json` to match.

Then read `~/.jarvis/jarvis.json` for existing tasks and their links.

## Step 3 — judge each tab

Four decisions per tab.

**Which project.** Match on topic, using their vocabulary from `profile.md` — not
on domain. Three GitHub tabs can belong to three different projects. If nothing
fits, `task_id: null` and it goes to "didn't fit anywhere". Never invent a project
to house one orphan tab.

**Reading or editing.** Editing means state lives in that tab and would be lost or
forgotten: an open PR under review, a doc in edit mode, a running localhost, a
half-filled form, a design file, a ticket mid-update. Reading means the page would
be identical if reopened tomorrow.

Anything with unsaved state is never closed. When genuinely torn, call it editing:
a wrongly-kept tab costs a glance, a wrongly-closed one costs a search.

**Why it was open.** One clause, concrete, in their register. *"Comparing retry
strategies for the payments queue"* — not *"Reference material"*. This sentence is
the whole value of the archive: it's what lets them decide in half a second
whether to reopen something. If you can't write a real one, that's a `low`
confidence signal, not a licence to write something vague and confident.

**Confidence.** `high` = obvious from title and URL. `medium` = a reasonable
inference. `low` = you're guessing. Low-confidence guesses are visually hedged on
the dashboard, which is fine. Confident-sounding wrong guesses are what make a
tool like this untrustworthy.

**Action.** `close` for reading, `keep` for editing. The protect list in
`config.json` is enforced by the script regardless of what you decide, so don't
check it yourself.

## Step 4 — apply

Write the classification to a temp file, then:

```bash
python3 scripts/apply.py /tmp/jarvis_pass.json
```

```json
{
  "tasks": [
    {"id": "short-slug", "title": "Their name for it",
     "kind": "project|watch|learning", "status": "active", "note": ""}
  ],
  "tabs": [
    {"url": "https://...", "title": "...", "mode": "reading|editing",
     "task_id": "short-slug", "why": "one concrete clause",
     "confidence": "high|medium|low", "action": "close|keep"}
  ]
}
```

`apply.py` writes every tab to disk **before** closing anything, skips protected
URLs, de-duplicates, re-renders, and opens the dashboard. Closing a tab never
loses it — it moves to the dashboard.

If `config.autonomous` is `false`, `apply.py` files everything but closes nothing
and prints the list it would have closed. Show that list and let them choose; if
they approve, flip `action` to `close` and run again, or close the URLs directly
with `scripts/close_tabs.py`.

## Step 5 — report

Two lines maximum:

> Swept 24 tabs — 18 filed and closed, 6 left open (mid-edit).
> Four things on the go; the payments work picked up 7 links.

## The dashboard is live and editable

Served by `scripts/serve.py` on `http://localhost:7777` (or `config.port`), bound
to localhost only. `apply.py` starts it automatically at the end of a sweep. The
page renders fresh from `jarvis.json` on every request, so **there is no re-render
step** — Refresh is the whole story.

The user can do all of this on the page, without you:

- **Get me back in** — reopens a task's tabs, editing ones first
- **Park / Unpark** — toggles a task out of the main view
- **Move to…** — reassigns a link to another task, or to unfiled
- **archive** — retires a link (recoverable; it goes to `archive`)
- **Notes** — click a task's note line and type; saves on blur

So don't offer to do these in chat when they're looking at the page. Chat is for
what the page can't do: sweeping, renaming, creating tasks, and judgment.

## Learning from corrections

When they push back — "that belongs to X", "stop closing that kind of thing",
"that isn't a project" — append one dated line to the **Corrections** section of
`profile.md`. Never edit or delete existing entries.

```
- 2026-09-12 — Pages under /spaces/ARCH are always the platform review, not the SDK work.
```

This is the mechanism by which Jarvis stops being annoying. If a correction
implies a machine-enforceable rule (a domain never to close), also add it to
`config.protect` — the log explains, the config enforces.

## Other things they may ask for

**"Just show me the dashboard"** — `python3 scripts/serve.py --quiet & open http://localhost:7777`. No sweep.

**"Get me back into X"** — they have a button for this. If they ask in chat anyway,
read `jarvis.json`, find the task, and `open -a "<browser_app>" <url> ...` — lead
with the `mode: editing` links. Reopen the handful that matter, not all of them.

**"Park X" / "X is done"** — also a button. In chat: set `status` to `parked` or
`done` in `jarvis.json`. The live page picks it up on refresh.

**Nothing to do** — if no tabs are open or everything's already filed, say so in
one line and don't run the pipeline.

## Judgment notes

- Duplicate tabs of one URL: file once, close all copies.
- A tab open in more than one window usually matters — keep it.
- Search result pages, blank new tabs, finished OAuth callbacks: close, don't file.
  They have no future value.
- If your classification produces ten `project`s, you've mistaken topics for
  projects — collapse them, or they belong in `watch`.
- Don't create tasks casually. A genuinely new project is something they'd tell
  you about, not something you'd infer from two tabs.
- Their stated parallel-thread count in `profile.md` is a sanity check on your
  output. Well above it means you're over-splitting.
