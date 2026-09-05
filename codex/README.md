# Jarvis on Codex

Jarvis is a single skill built on the [open agent skills standard](https://agentskills.io),
so Codex runs the same `SKILL.md` and the same Python scripts as Claude Code.
There is no separate port to maintain.

## Install

```bash
./install.sh codex     # or: ./install.sh both
```

That copies the skill to `~/.agents/skills/jarvis/` — Codex's user-scope skill
location — and creates your data directory at `~/.jarvis/`.

To check in a repo-scoped copy for a team instead, put it at
`.agents/skills/jarvis/` in the repository root.

## Use

```
$jarvis
```

Codex skills are invoked with `$name` rather than `/name`. `/skills` lists what's
installed.

Implicit invocation is **off** by default, set in `agents/openai.yaml`. Jarvis
closes browser tabs, and that should happen because you asked for it — not
because a prompt happened to sound tab-adjacent. If you'd rather Codex reach for
it on its own, change `allow_implicit_invocation` to `true` in
`~/.agents/skills/jarvis/agents/openai.yaml` and restart Codex.

## Differences from Claude Code

| | Claude Code | Codex |
|---|---|---|
| Install path | `~/.claude/skills/jarvis/` | `~/.agents/skills/jarvis/` |
| Invocation | `/jarvis` | `$jarvis` |
| Implicit triggering | on | off by default |
| Extra metadata | ignored | `agents/openai.yaml` |

Data (`~/.jarvis/profile.md`, `jarvis.json`, `config.json`) is shared. Install
both and they see the same dashboard and the same history.

## AGENTS.md

You don't need one — the skill is self-contained. If you want Codex to know
Jarvis exists without you invoking it, add this to `~/.agents/AGENTS.md`:

```markdown
## Tabs and focus

Jarvis (`$jarvis`) sweeps open browser tabs, files them against my current
projects, and maintains a dashboard at http://localhost:7777.
My working context lives in ~/.jarvis/profile.md — read it before reasoning
about what I'm working on.
```

That last line is the useful part: it makes your profile available to Codex for
ordinary questions, not just during a sweep.

## Troubleshooting

**Skill doesn't appear** — restart Codex; it caches the skill list at startup.
Confirm with `/skills`.

**Disable without uninstalling** — in `~/.codex/config.toml`:

```toml
[[skills.config]]
path = "/Users/you/.agents/skills/jarvis/SKILL.md"
enabled = false
```

**"Can't see any tabs"** — same cause as on Claude Code: macOS Automation
permission. See the main README.
