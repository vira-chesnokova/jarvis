# Onboarding

Read this only when `profile.md` has no projects in it, or when the user asks to
set Jarvis up again. Then return to `SKILL.md` and run a normal sweep.

## What you are trying to produce

A filled-in `~/.jarvis/profile.md` and a seeded `~/.jarvis/jarvis.json`. Nothing
else. If you get their projects and vocabulary right, everything downstream works;
if you get them wrong, no amount of clever classification will save it.

## The one rule

**Never ask for anything you can detect, and never ask them to compose from a
blank page.** Detect what you can, draft from it, and let them react. Reacting to
a wrong draft costs a fraction of what writing a right one does — and this is a
tool whose entire premise is protecting their attention. An onboarding that drains
them has already broken its promise.

Budget: **four messages, roughly two minutes.** If you're heading past that,
you're interrogating. Stop and write the profile with what you have — they can
correct it later, and the Corrections log is designed for exactly that.

Never ask about file paths, JSON schemas, ports, or config keys. Those are
detected or defaulted. Ask only about *them*.

---

## Message 1 — detect, then ask two questions

First, silently gather evidence:

```bash
python3 scripts/read_tabs.py --which     # which browser is actually running
python3 scripts/read_tabs.py             # what's open right now
```

Also glance at obvious context you already have: the current directory, a git
remote, a `~/Documents` or notes folder if one is plainly visible. Don't go
hunting across their filesystem — it's slow and it's creepy.

Then ask, in one message, exactly two questions:

1. **What are you accountable for?** What would people come to you about?
2. **What are the 3–5 things actually on your plate right now?** For each, roughly:
   what does *done* look like, and why does it matter this month?

Say plainly that they can answer messily, in any order, in one dump — you'll do
the structuring. Do not number sub-questions or ask for a specific format.

If their open tabs suggest obvious candidates, offer them *as a prompt to react
to*, not as an answer:

> Looks like you might have something going on with the billing migration and
> something Kubernetes-shaped — but tabs lie, so tell me what's actually on your
> plate.

## Message 2 — propose a structured draft

Turn their dump into a draft and show it back. Sort every item into one of the
three buckets from `SKILL.md`:

- `project` — has an end state
- `watch` — a standing duty, never finishes, must not surprise them
- `learning` — deliberate side study, zero pressure

Getting this split right is the highest-value thing you do here. People list
"following the Q3 deals" in the same breath as "shipping the redesign", and
flattening those into one list is what makes a dashboard feel heavy.

Show the draft compactly — name, bucket, and where they gave one, the done-state.
Then ask one question: **what's wrong with this?** Not "is this right?" — inviting
correction gets better results than inviting approval.

Also propose a vocabulary table from their language: product names, repo names,
acronyms, team names, and which project each belongs to. Say you're guessing.

## Message 3 — guardrails

Three short questions, and make clear they can skip any of them:

1. **What should never be closed, no matter what?** Their mail, calendar, chat,
   anything they keep open from habit. Say that unsaved-state tabs are already
   protected so they don't need to list those.
2. **Coming back to a task after a few days, what do you need first** — where you
   left off, the reference set, or why it mattered? This changes what the
   dashboard puts on top.
3. **Confirm the browser** you detected, if there was any ambiguity.

If they detected as using something other than stock Chrome, set `browser_app` in
`config.json` yourself. Don't make them edit JSON.

## Message 4 — write, then sweep

Write `~/.jarvis/profile.md` in full: Role, Current projects, Keeping an eye on,
Learning, Vocabulary, How I work, Never close. Leave the Corrections section
empty with its comment intact.

Seed `~/.jarvis/jarvis.json` with one task per item, correct `kind`, empty
`links`. Use `apply.py` with a `tasks` array and no `tabs`, or write the file
directly — both are fine.

Put their protected URLs into `config.protect`.

Then say one thing about autonomy, because it's the only surprising behaviour:

> Jarvis closes tabs it decides you're done reading. Nothing is lost — every tab
> is written to the dashboard before it closes. If you'd rather approve the list
> first, say so and I'll switch it.

Then run a normal sweep from `SKILL.md`.

---

## Adapting to who they are

The two questions are the same for everyone, but the *examples* you offer should
match the evidence. Someone with GitHub, Jira and Datadog tabs is not living the
same week as someone with Figma, Notion and a course platform. Draw your example
project names from their own tabs, never from a generic list.

Some people have no `project` items at all — only standing duties and learning.
That's a legitimate shape, not an incomplete answer. Don't push them to invent a
project so the dashboard looks fuller.

Some people will give you one enormous project. Ask once whether it splits; if
they say no, accept it.

## When the profile is thin

If they give you almost nothing — "I'm a developer, I dunno, stuff" — don't
interrogate. Write what you have, seed a single `watch` task called something
honest like "Unsorted", and run the sweep. The first dashboard, even a rough one,
teaches them more about what Jarvis wants than three more questions would. Say:

> This will be rough until I know your projects. Tell me when I file something
> wrong and I'll learn it permanently.

That is true — the Corrections log makes it true — and it converts a bad
onboarding into a good second week.
