# Jarvis

**Your tabs are a to-do list you never wrote down. Jarvis reads it, files it, and closes it.**

A skill for [Claude Code](https://claude.com/claude-code) and [Codex](https://developers.openai.com/codex/).
It sweeps your open browser tabs, works out which of your projects each one belongs
to, closes the ones you've finished reading, and keeps a live dashboard of what
you're actually working on.

> **macOS only.** Jarvis reads your tabs through AppleScript. On Linux and Windows
> it will install and then do nothing. There is no workaround yet — see
> [Limitations](#limitations).

![The Jarvis dashboard](docs/dashboard.png)

---

## The idea

Thirty open tabs is not a browser problem, it's a memory problem. Each one is a
thing you meant to come back to, and the reason you opened it is decaying in your
head. By Thursday you can't close them (what if they mattered?) and you can't use
them (which one was the useful one?). So they sit there, costing attention and
paying nothing.

Jarvis empties them into something you can actually read:

- **Every tab gets filed** against a project, with one line saying why you had it
  open. That sentence is the whole point — it's what lets you decide in half a
  second whether to reopen something.
- **Reading tabs get closed.** Anything with unsaved state stays.
- **The dashboard leads with where you left off**, so re-entering a project takes
  a click instead of ten minutes of reconstruction.

**Nothing is ever lost.** Every tab is written to disk *before* anything closes.
"Closed" means "moved to the dashboard".

## Install

```bash
git clone https://github.com/vira-chesnokova/jarvis.git
cd jarvis
./install.sh          # Claude Code
./install.sh codex    # Codex
./install.sh both
```

Or as a Claude Code plugin:

```
/plugin marketplace add vira-chesnokova/jarvis
/plugin install jarvis
```

Then open your agent and run `/jarvis` (Codex: `$jarvis`).

**macOS will ask permission** for your terminal to control your browser the first
time. Without it Jarvis can't see any tabs. If you dismissed the prompt:
System Settings → Privacy & Security → Automation.

## First run

Jarvis doesn't know you yet, so it asks — twice, briefly. What you're accountable
for, and what's actually on your plate. It uses your open tabs to draft an answer
you can correct rather than making you fill in a blank page. Two minutes, once.

That becomes `~/.jarvis/profile.md`: your role, your projects, your vocabulary.
It's read before every sweep, and it's plain markdown you can edit any time.

## What it does with a tab

For each one it decides four things:

| | |
|---|---|
| **Which project** | Matched on topic using your vocabulary — not on domain. Three GitHub tabs can belong to three different projects. |
| **Reading or editing** | Editing means state lives in that tab. Those stay open, always. |
| **Why you had it open** | One concrete clause. *"Working out idempotency on retries"*, not *"Reference material"*. |
| **How sure it is** | Low-confidence guesses are visually hedged, so a guess reads as a guess. |

Then reading tabs are filed and closed, editing tabs are left alone, and the
dashboard rebuilds.

### Three buckets, not one list

Things you're *doing* and things you're *keeping an eye on* are different species,
and flattening them into one list is what makes a dashboard feel heavy.

- **Projects** — have an end state. Counted, at the top, full cards.
- **Keeping an eye on** — standing duties that never finish. Quiet rows, not counted.
- **Learning** — deliberate side study. Quiet, never above real work.

## The dashboard

Runs at `http://localhost:7777`, bound to localhost, started automatically after a
sweep. Stdlib Python — no dependencies, no build step, nothing phones home.

It's editable. **Get me back in** reopens a project's tabs, editing ones first.
**Move to…** refiles a link. **Park** hides a project. **archive** retires a link.
Task notes are click-and-type. Every write is atomic.

## It learns

When you say *"no, that belongs to the billing work"*, Jarvis appends a dated line
to the **Corrections** section of your profile. That log outranks its own judgment
on every future run. Corrections are never rewritten or pruned — it's why the tool
gets less annoying instead of more.

## Autonomy

**By default Jarvis closes tabs without asking**, from the very first run. That's a
deliberate choice: a tool that asks permission thirty times isn't saving you
anything. The safety isn't confirmation, it's that closing is non-destructive —
the tab is already on your dashboard with a note explaining why you had it.

If you'd rather approve the list first, set `"autonomous": false` in
`~/.jarvis/config.json`. Jarvis will file everything and show you what it *would*
have closed.

Some things are never closed, enforced in code rather than by judgment:

- anything matching `protect` in your config (add your mail, chat, calendar)
- anything with unsaved state — forms, drafts, editors, localhost
- anything on a browser that isn't running

## Your data

Everything lives in `~/.jarvis/`, in plain text you can read and edit:

| File | What |
|---|---|
| `profile.md` | Who you are, your projects, your vocabulary, your corrections |
| `jarvis.json` | Tasks, filed links, archive |
| `config.json` | Protected URLs, browser choice, port, autonomy |

It never leaves your machine. The dashboard binds to `127.0.0.1`. Reinstalling
doesn't touch any of it.

## Configuration

```jsonc
{
  "browser_app": "Google Chrome",   // or Brave Browser, Arc, Microsoft Edge, Chromium…
  "protect": ["mail.google.com", "app.slack.com", "localhost"],
  "autonomous": true,               // false = propose, don't close
  "port": 7777,
  "knowledge": {
    "github": "",                   // optional KB repo, read for vocabulary
    "folders": []                   // optional local folders to skim
  }
}
```

Not sure which browser to name? `python3 ~/.claude/skills/jarvis/scripts/read_tabs.py --which`
lists the ones actually running.

## Limitations

- **macOS only.** AppleScript is the entire tab-reading mechanism. A cross-platform
  version would need a browser extension — contributions welcome.
- **Chromium browsers only.** Safari and Firefox aren't scriptable the same way.
- **URL and title only.** Jarvis doesn't read page contents, which keeps it fast
  and private but means classification leans on titles being informative.
- **One profile.** No separate work/personal modes yet.

## Troubleshooting

**"Nothing to sweep" but you have tabs open** — run
`python3 ~/.claude/skills/jarvis/scripts/read_tabs.py --debug`. It reports window
count, tab count, how many were blank, and how many were unreadable. Usually it's
the Automation permission, or a browser named something other than "Google Chrome".

**Port 7777 is taken** — change `port` in `config.json`.

**Filing is wrong** — tell it so, in chat. That's the Corrections mechanism, and
it's more effective than editing JSON. If your profile's vocabulary section is
thin, filling it in helps more than anything else.

## Contributing

Issues and PRs welcome. The highest-value contributions right now:

1. A cross-platform tab reader (browser extension or native messaging host).
2. Safari and Firefox support.
3. Better first-run onboarding for people who aren't knowledge workers.

## Licence

MIT — see [LICENSE](LICENSE).
