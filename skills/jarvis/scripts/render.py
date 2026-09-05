#!/usr/bin/env python3
"""Render jarvis.json into the dashboard.

Static:  render.py [jarvis.json] [output.html]   -> plain read-only page
Served:  imported by serve.py with interactive=True -> buttons and editing

Defaults: ~/.jarvis/jarvis.json  ->  ~/.jarvis/dashboard.html
"""
import html
import json
import os
import sys
from datetime import datetime

HOME = os.path.expanduser("~")
DATA = os.path.join(HOME, ".jarvis", "jarvis.json")
OUT = os.path.join(HOME, ".jarvis", "dashboard.html")

CSS = """
:root {
  --bg: #faf9f7; --surface: #ffffff; --line: #e8e4dd;
  --ink: #23211e; --ink-soft: #6b665e; --ink-faint: #9c968c;
  --accent: #3d6b5c; --accent-soft: #eef3f1; --warm: #b5813f;
  --radius: 10px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16151a; --surface: #1d1c22; --line: #2e2c35;
    --ink: #e8e5e0; --ink-soft: #a09b94; --ink-faint: #6f6a63;
    --accent: #7db8a3; --accent-soft: #212b28; --warm: #d5a463;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 760px; margin: 0 auto; padding: 56px 24px 120px; }

header { margin-bottom: 48px; }
.brandrow { display: flex; align-items: center; gap: 14px; }
h1 {
  font-size: 15px; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--ink-faint); margin: 0; flex: 1;
}
.summary { font-size: 24px; line-height: 1.4; margin: 12px 0 0; font-weight: 400; }
.summary em { font-style: normal; color: var(--accent); font-weight: 600; }
.stamp { margin: 12px 0 0; font-size: 13px; color: var(--ink-faint); }

.task {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 20px 22px; margin-bottom: 12px;
}
.task-head { display: flex; align-items: baseline; gap: 12px; }
.task h2 { font-size: 17px; font-weight: 600; margin: 0; flex: 1; line-height: 1.35; }
.note { margin: 8px 0 0; font-size: 14px; color: var(--ink-soft); }

details { margin-top: 14px; }
details > summary {
  cursor: pointer; font-size: 13px; color: var(--accent); list-style: none;
  display: inline-flex; align-items: center; gap: 6px; padding: 3px 0; user-select: none;
}
details > summary::-webkit-details-marker { display: none; }
details > summary::before {
  content: "\\203A"; display: inline-block; transition: transform .15s ease;
  font-size: 15px; line-height: 1;
}
details[open] > summary::before { transform: rotate(90deg); }
details > summary:hover { text-decoration: underline; }

ul.links { list-style: none; margin: 12px 0 0; padding: 0; }
ul.links li { padding: 11px 0; border-top: 1px solid var(--line); }
ul.links li:first-child { border-top: none; padding-top: 4px; }
ul.links a {
  color: var(--ink); text-decoration: none; font-size: 14.5px;
  display: block; line-height: 1.45;
}
ul.links a:hover { color: var(--accent); text-decoration: underline; }
.why { margin: 3px 0 0; font-size: 13px; color: var(--ink-soft); }
.host { font-size: 12px; color: var(--ink-faint); margin: 2px 0 0; }
.hedge { color: var(--warm); font-style: italic; }

.resume { margin-top: 14px; padding: 12px 16px; background: var(--accent-soft); border-radius: 8px; }
.resume-label {
  margin: 0 0 6px; font-size: 11px; font-weight: 600; letter-spacing: .1em;
  text-transform: uppercase; color: var(--accent);
}
.resume ul.links li { border-top-color: rgba(128,128,128,.18); }
.resume ul.links a { font-weight: 500; }

/* --- controls (served mode only) --- */
.btn {
  font: inherit; font-size: 13px; line-height: 1;
  padding: 7px 13px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink-soft);
  transition: all .12s ease;
}
.btn:hover { border-color: var(--accent); color: var(--accent); }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 500; }
.btn.primary:hover { filter: brightness(1.08); color: #fff; }
.btn.ghost { border-color: transparent; padding: 5px 8px; color: var(--ink-faint); font-size: 12px; }
.btn.ghost:hover { color: var(--warm); border-color: transparent; }
.controls { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
.link-ctl { display: flex; gap: 6px; align-items: center; margin-top: 6px; }
.link-ctl select {
  font: inherit; font-size: 12px; padding: 3px 6px; border-radius: 6px;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink-faint);
}
.task.quiet .controls { margin-top: 10px; }

.task.quiet {
  background: none; border: none; border-bottom: 1px solid var(--line);
  border-radius: 0; padding: 15px 2px; margin-bottom: 0;
}
.task.quiet h2 { font-size: 15px; font-weight: 500; color: var(--ink-soft); }
.task.quiet .note { font-size: 13px; }
.unsorted { background: none; border: 1px dashed var(--line); }

.section-label {
  font-size: 12px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
  color: var(--ink-faint); margin: 44px 0 14px;
}
.empty {
  color: var(--ink-soft); font-size: 15px; text-align: center;
  padding: 48px 24px; border: 1px dashed var(--line); border-radius: var(--radius);
}
footer {
  margin-top: 64px; padding-top: 20px; border-top: 1px solid var(--line);
  font-size: 12.5px; color: var(--ink-faint);
}
footer code { font-size: 12px; background: var(--accent-soft); padding: 2px 6px; border-radius: 4px; color: var(--accent); }
#toast {
  position: fixed; bottom: 26px; left: 50%; transform: translateX(-50%) translateY(20px);
  background: var(--ink); color: var(--bg); padding: 10px 18px; border-radius: 999px;
  font-size: 13.5px; opacity: 0; pointer-events: none; transition: all .2s ease;
}
#toast.on { opacity: 1; transform: translateX(-50%) translateY(0); }
"""

JS = """
async function api(path, body) {
  const r = await fetch(path, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body || {})
  });
  if (!r.ok) { toast('Something went wrong'); return null; }
  return r.json();
}
let tid;
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg; el.classList.add('on');
  clearTimeout(tid); tid = setTimeout(() => el.classList.remove('on'), 1900);
}
document.addEventListener('click', async (e) => {
  const b = e.target.closest('[data-act]');
  if (!b || b.tagName === 'SELECT') return;
  e.preventDefault();
  const act = b.dataset.act;
  if (act === 'resume') {
    b.disabled = true;
    const r = await api('/api/resume', {task_id: b.dataset.task});
    b.disabled = false;
    toast(r && r.opened ? `Opening ${r.opened} tab${r.opened === 1 ? '' : 's'}` : 'Nothing to reopen');
  } else if (act === 'park') {
    await api('/api/park', {task_id: b.dataset.task}); location.reload();
  } else if (act === 'archive') {
    await api('/api/archive', {task_id: b.dataset.task, url: b.dataset.url}); location.reload();
  } else if (act === 'refresh') {
    location.reload();
  }
});
document.addEventListener('change', async (e) => {
  const s = e.target.closest('select[data-act="move"]');
  if (!s || !s.value) return;
  await api('/api/move', {from: s.dataset.task, to: s.value, url: s.dataset.url});
  location.reload();
});
document.addEventListener('blur', async (e) => {
  const n = e.target.closest('[data-note]');
  if (!n) return;
  await api('/api/note', {task_id: n.dataset.note, note: n.textContent.trim()});
  toast('Saved');
}, true);
"""


def esc(s):
    return html.escape(str(s or ""))


def host(url):
    try:
        h = url.split("//", 1)[-1].split("/", 1)[0]
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


def move_select(task_id, url, options):
    opts = "".join(
        f'<option value="{esc(i)}">{esc(t)}</option>'
        for i, t in options if i != task_id
    )
    return (
        f'<select data-act="move" data-task="{esc(task_id)}" data-url="{esc(url)}">'
        f'<option value="">Move to&hellip;</option>{opts}</select>'
    )


def link_li(l, task_id=None, options=None, hedge=True):
    why = esc(l.get("why", ""))
    if hedge and l.get("confidence") == "low" and why:
        why = f'<span class="hedge">maybe: {why}</span>'
    why_html = f'<p class="why">{why}</p>' if why else ""
    url = l.get("url", "")
    ctl = ""
    if options is not None:
        ctl = (
            '<div class="link-ctl">'
            + move_select(task_id, url, options)
            + f'<button class="btn ghost" data-act="archive" '
            f'data-task="{esc(task_id)}" data-url="{esc(url)}">archive</button></div>'
        )
    return (
        "<li>"
        f'<a href="{esc(url)}" target="_blank" rel="noopener">'
        f'{esc(l.get("title") or url)}</a>{why_html}'
        f'<p class="host">{esc(host(url))}</p>{ctl}</li>'
    )


def task_block(t, quiet=False, options=None):
    links = t.get("links", [])
    tid = t.get("id", "")
    interactive = options is not None

    note_txt = esc(t.get("note", ""))
    if interactive:
        note = (
            f'<p class="note" contenteditable="true" data-note="{esc(tid)}" '
            f'>{note_txt}</p>' if note_txt else
            f'<p class="note" contenteditable="true" data-note="{esc(tid)}" '
            f'style="color:var(--ink-faint)"></p>'
        )
    else:
        note = f'<p class="note">{note_txt}</p>' if note_txt else ""

    # Most people re-enter a task at whatever they were mid-way through, so
    # editing tabs sit above the fold and reference material collapses.
    resume = [l for l in links if l.get("mode") == "editing"]
    rest = [l for l in links if l.get("mode") != "editing"]

    resume_html = ""
    if resume:
        items = "".join(link_li(l, tid, options, hedge=False) for l in resume)
        resume_html = (
            '<div class="resume"><p class="resume-label">You were here</p>'
            f'<ul class="links">{items}</ul></div>'
        )

    n = len(rest)
    if n:
        label = (f"{n} more link" if resume else f"{n} link") + ("" if n == 1 else "s")
        items = "".join(link_li(l, tid, options) for l in rest)
        rest_html = (
            f"<details><summary>{label}</summary>"
            f'<ul class="links">{items}</ul></details>'
        )
    elif not resume:
        rest_html = '<p class="note" style="margin-top:10px">no links yet</p>'
    else:
        rest_html = ""

    ctrl = ""
    if interactive:
        parked = t.get("status", "active") != "active"
        park_label = "Unpark" if parked else "Park"
        resume_btn = (
            f'<button class="btn primary" data-act="resume" data-task="{esc(tid)}">'
            "Get me back in</button>" if links else ""
        )
        ctrl = (
            f'<div class="controls">{resume_btn}'
            f'<button class="btn" data-act="park" data-task="{esc(tid)}">{park_label}</button>'
            "</div>"
        )

    cls = "task quiet" if quiet else "task"
    return (
        f'<article class="{cls}">'
        f'<div class="task-head"><h2>{esc(t.get("title"))}</h2></div>'
        f"{note}{resume_html}{rest_html}{ctrl}</article>"
    )


def render(data, interactive=False):
    tasks = data.get("tasks", [])
    live = [t for t in tasks if t.get("status", "active") == "active"]
    active = [t for t in live if t.get("kind", "project") == "project"]
    watch = [t for t in live if t.get("kind") == "watch"]
    learning = [t for t in live if t.get("kind") == "learning"]
    resting = [t for t in tasks if t.get("status", "active") != "active"]
    unfiled = data.get("unfiled", [])
    run = data.get("last_run") or {}

    options = None
    if interactive:
        options = [(t["id"], t.get("title", t["id"])) for t in tasks]
        options.append(("__unfiled__", "— Unfiled —"))

    # Only real projects count. Standing duties aren't a number to carry.
    n = len(active)
    summary = (
        f"You have <em>{n}</em> thing{'' if n == 1 else 's'} on the go."
        if active else "Nothing on the go."
    )

    stamp_bits = []
    if run.get("at"):
        try:
            d = datetime.fromisoformat(run["at"])
            stamp_bits.append("Swept " + d.strftime("%-d %b, %-I:%M %p").lower())
        except Exception:
            stamp_bits.append("Swept " + str(run["at"]))
    if run.get("tabs_seen") is not None:
        stamp_bits.append(
            f"{run.get('tabs_seen', 0)} tabs · {run.get('closed', 0)} closed · "
            f"{run.get('kept', 0)} left open"
        )
    stamp = " · ".join(stamp_bits)

    refresh = (
        '<button class="btn" data-act="refresh">Refresh</button>' if interactive else ""
    )

    parts = [
        '<div class="wrap"><header>',
        f'<div class="brandrow"><h1>Jarvis</h1>{refresh}</div>',
        f'<p class="summary">{summary}</p>',
        f'<p class="stamp">{esc(stamp)}</p>' if stamp else "",
        "</header><main>",
    ]

    if active:
        parts += [task_block(t, options=options) for t in active]
    else:
        parts.append(
            '<p class="empty">No active projects yet. Run <code>/jarvis</code> '
            "in Claude Code to sweep your tabs.</p>"
        )

    if watch:
        parts.append('<p class="section-label">Keeping an eye on</p>')
        parts += [task_block(t, quiet=True, options=options) for t in watch]

    if learning:
        parts.append('<p class="section-label">Learning</p>')
        parts += [task_block(t, quiet=True, options=options) for t in learning]

    if resting:
        parts.append('<p class="section-label">Parked</p>')
        inner = "".join(task_block(t, quiet=True, options=options) for t in resting)
        parts.append(
            f'<details><summary>{len(resting)} parked</summary>'
            f'<div style="margin-top:12px">{inner}</div></details>'
        )

    if unfiled:
        parts.append('<p class="section-label">Didn&rsquo;t fit anywhere</p>')
        items = "".join(link_li(l, "__unfiled__", options) for l in unfiled)
        parts.append(
            '<article class="task unsorted">'
            f'<details><summary>{len(unfiled)} saved, unsorted</summary>'
            f'<ul class="links">{items}</ul></details></article>'
        )

    arch = len(data.get("archive", []))
    foot = f"{arch} link{'' if arch == 1 else 's'} archived"
    foot += " · run <code>/jarvis</code> in Claude Code to sweep" if interactive \
        else " · data at ~/.jarvis/jarvis.json"
    parts.append(f"</main><footer>{foot}</footer></div>")

    script = f'<div id="toast"></div><script>{JS}</script>' if interactive else ""

    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Jarvis</title>"
        f"<style>{CSS}</style></head><body>"
        + "".join(parts) + script + "</body></html>"
    )


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else DATA
    dst = sys.argv[2] if len(sys.argv) > 2 else OUT
    with open(src, encoding="utf-8") as fh:
        data = json.load(fh)
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(render(data))
    print(dst)
