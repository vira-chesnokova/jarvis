#!/usr/bin/env python3
"""The Jarvis dashboard, live. Stdlib only, bound to localhost.

    python3 serve.py            # foreground, prints the URL
    python3 serve.py --quiet    # no banner (used when auto-started)

The page is rendered fresh from jarvis.json on every request, so there is no
separate "re-render" step — Refresh is the whole story.

Endpoints (all POST, all local):
    /api/resume   {task_id}                -> reopen a task's tabs in Chrome
    /api/open     {url}                    -> open one stored link (file:// included)
    /api/park     {task_id}                -> toggle active <-> parked
    /api/move     {from, to, url}          -> move a link between tasks
    /api/archive  {task_id, url}           -> retire a link (recoverable)
    /api/note     {task_id, note}          -> save an inline note
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render  # noqa: E402

HOME = os.path.expanduser("~")
JDIR = os.path.join(HOME, ".jarvis")
DATA = os.path.join(JDIR, "jarvis.json")
CONFIG = os.path.join(JDIR, "config.json")
PORT = 7777  # default; config["port"] wins


def cfg(key, default=None):
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            v = json.load(fh).get(key)
            return default if v in (None, "") else v
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return default


def browser():
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            return json.load(fh).get("browser_app") or "Google Chrome"
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return "Google Chrome"

def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def open_urls(urls):
    """Open urls as tabs in the browser. Returns how many were handed over.

    Uses AppleScript rather than `open -a`: macOS `open` exits 0 but silently
    does nothing when it hands Chrome a file:// url, which would quietly drop
    every local file from a resume with no error to notice.
    """
    urls = [u for u in urls if u]
    if not urls:
        return 0
    items = ", ".join(f'"{_esc(u)}"' for u in urls)
    script = f'''
set targets to {{{items}}}
tell application "{browser()}"
	activate
	if (count of windows) is 0 then make new window
	repeat with u in targets
		tell front window to make new tab with properties {{URL:u}}
	end repeat
end tell
'''
    try:
        p = subprocess.run(["osascript", "-e", script],
                           capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0
    return len(urls) if p.returncode == 0 else 0


_lock = threading.Lock()


def load():
    try:
        with open(DATA, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": 1, "last_run": None, "tasks": [], "unfiled": [], "archive": []}


def save(data):
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA)  # atomic - a crash mid-write can't corrupt the store


def bucket(data, task_id):
    """Return the list of links for a task id, or the unfiled list."""
    if task_id == "__unfiled__":
        return data.setdefault("unfiled", [])
    for t in data.get("tasks", []):
        if t["id"] == task_id:
            return t.setdefault("links", [])
    return None


def pop_link(data, task_id, url):
    b = bucket(data, task_id)
    if b is None:
        return None
    for i, l in enumerate(b):
        if l.get("url") == url:
            return b.pop(i)
    return None


# --- actions ---------------------------------------------------------------

def act_resume(data, body):
    b = bucket(data, body.get("task_id"))
    if not b:
        return {"opened": 0}
    # Lead with where she left off; reference material follows.
    ordered = [l for l in b if l.get("mode") == "editing"] + \
              [l for l in b if l.get("mode") != "editing"]
    urls = [l["url"] for l in ordered[:12] if l.get("url")]
    return {"opened": open_urls(urls)}


def known_urls(data):
    """Every url Jarvis is currently holding, wherever it lives."""
    seen = {l.get("url") for l in data.get("unfiled", [])}
    seen |= {l.get("url") for l in data.get("archive", [])}
    for t in data.get("tasks", []):
        seen |= {l.get("url") for l in t.get("links", [])}
    return seen


def act_open(data, body):
    """Open one stored link in the browser.

    Chrome refuses to navigate from an http:// page to a file:// url, so a
    local file can only be reached by asking the host to open it. Restricted
    to urls already in the store, so a stray page POSTing here cannot open
    anything Jarvis was not already holding.
    """
    url = body.get("url")
    if not url or url not in known_urls(data):
        return {"error": "unknown link"}
    return {"opened": open_urls([url])}


def act_park(data, body):
    for t in data.get("tasks", []):
        if t["id"] == body.get("task_id"):
            t["status"] = "parked" if t.get("status", "active") == "active" else "active"
            return {"status": t["status"]}
    return {"error": "no such task"}


def act_move(data, body):
    link = pop_link(data, body.get("from"), body.get("url"))
    if link is None:
        return {"error": "link not found"}
    dest = bucket(data, body.get("to"))
    if dest is None:
        bucket(data, body.get("from")).append(link)  # put it back
        return {"error": "no such destination"}
    if not any(l.get("url") == link.get("url") for l in dest):
        dest.append(link)
    return {"ok": True}


def act_archive(data, body):
    link = pop_link(data, body.get("task_id"), body.get("url"))
    if link is None:
        return {"error": "link not found"}
    data.setdefault("archive", []).append(link)
    return {"ok": True}


def act_note(data, body):
    for t in data.get("tasks", []):
        if t["id"] == body.get("task_id"):
            t["note"] = (body.get("note") or "")[:400]
            return {"ok": True}
    return {"error": "no such task"}


ACTIONS = {
    "/api/resume": act_resume,
    "/api/open": act_open,
    "/api/park": act_park,
    "/api/move": act_move,
    "/api/archive": act_archive,
    "/api/note": act_note,
}
# Reading the store is enough for resume; the rest mutate and must be persisted.
READ_ONLY = {"/api/resume", "/api/open"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silence the default request log

    def _send(self, code, body, ctype="application/json"):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html"):
            self._send(404, json.dumps({"error": "not found"}))
            return
        self._send(200, render(load(), interactive=True), "text/html")

    def do_POST(self):
        path = self.path.split("?")[0]
        action = ACTIONS.get(path)
        if not action:
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send(400, json.dumps({"error": "bad request"}))
            return
        with _lock:
            data = load()
            result = action(data, body)
            if path not in READ_ONLY and "error" not in result:
                save(data)
        self._send(200, json.dumps(result))


def main():
    quiet = "--quiet" in sys.argv
    os.makedirs(JDIR, exist_ok=True)
    port = int(cfg("port", PORT))
    try:
        # 127.0.0.1, never 0.0.0.0 - this is not for the network.
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        if not quiet:
            print(f"Port {port} is busy - Jarvis is probably already running:")
            print(f"  http://localhost:{port}")
        return
    if not quiet:
        print(f"Jarvis dashboard: http://localhost:{port}   (ctrl-c to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
