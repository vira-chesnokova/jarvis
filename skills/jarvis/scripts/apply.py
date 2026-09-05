#!/usr/bin/env python3
"""Apply a classification pass: merge into jarvis.json, close tabs, re-render.

Usage: apply.py classification.json

classification.json shape:
{
  "tasks": [ {"id": "slug", "title": "...", "kind": "project", "status": "active", "note": ""} ],
  "tabs": [
    {"url": "...", "title": "...", "mode": "reading|editing",
     "task_id": "slug" | null,
     "why": "short reason this was open",
     "confidence": "high|medium|low",
     "action": "close|keep"}
  ]
}

Rules enforced here (not left to judgment):
  - a tab matching config["protect"] is never closed
  - every tab is written to jarvis.json BEFORE anything is closed
  - a link already stored for the same task is not duplicated
"""
import json
import os
import subprocess
import sys
from datetime import datetime

HOME = os.path.expanduser("~")
JDIR = os.path.join(HOME, ".jarvis")
DATA = os.path.join(JDIR, "jarvis.json")
CONFIG = os.path.join(JDIR, "config.json")
HERE = os.path.dirname(os.path.abspath(__file__))


def load(path, fallback):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def protected(url, patterns):
    return any(p and p.lower() in url.lower() for p in patterns)


def main(cls_path):
    cls = load(cls_path, None)
    if cls is None:
        sys.exit(f"Could not read classification file: {cls_path}")

    os.makedirs(JDIR, exist_ok=True)
    data = load(DATA, {"version": 1, "last_run": None,
                       "tasks": [], "unfiled": [], "archive": []})
    config = load(CONFIG, {})
    protect = config.get("protect", [])
    today = datetime.now().strftime("%Y-%m-%d")

    # --- merge task definitions -------------------------------------------
    by_id = {t["id"]: t for t in data["tasks"]}
    for t in cls.get("tasks", []):
        if t["id"] in by_id:
            existing = by_id[t["id"]]
            existing["title"] = t.get("title", existing["title"])
            if t.get("status"):
                existing["status"] = t["status"]
            if t.get("kind"):
                existing["kind"] = t["kind"]
            if t.get("note"):
                existing["note"] = t["note"]
        else:
            fresh = {
                "id": t["id"],
                "title": t.get("title", t["id"]),
                "kind": t.get("kind", "project"),
                "status": t.get("status", "active"),
                "note": t.get("note", ""),
                "links": [],
                "created": today,
            }
            data["tasks"].append(fresh)
            by_id[t["id"]] = fresh

    # --- file every tab ----------------------------------------------------
    to_close, proposed, kept, filed = [], [], 0, 0
    seen_unfiled = {l["url"] for l in data.get("unfiled", [])}

    for tab in cls.get("tabs", []):
        url = (tab.get("url") or "").strip()
        if not url:
            continue
        entry = {
            "url": url,
            "title": tab.get("title", ""),
            "why": tab.get("why", ""),
            "confidence": tab.get("confidence", "medium"),
            "mode": tab.get("mode", "reading"),
            "added": today,
        }

        tid = tab.get("task_id")
        if tid and tid in by_id:
            task = by_id[tid]
            if not any(l["url"] == url for l in task["links"]):
                task["links"].append(entry)
            filed += 1
        else:
            if url not in seen_unfiled:
                data.setdefault("unfiled", []).append(entry)
                seen_unfiled.add(url)
            filed += 1

        if tab.get("action") == "close" and not protected(url, protect):
            to_close.append(url)
        else:
            kept += 1

    # In non-autonomous mode nothing is touched: everything is already filed,
    # so the agent can show the list and let the user decide.
    if not config.get("autonomous", True):
        proposed, to_close = to_close, []
        kept += len(proposed)  # they stay open, so the report must say so

    # --- only now touch the browser ---------------------------------------
    closed = 0
    if proposed:
        print(f"Would close {len(proposed)} tab(s) - autonomous mode is off.")
        for u in proposed:
            print(f"  {u}")
    if to_close:
        listfile = os.path.join(JDIR, ".to_close.txt")
        with open(listfile, "w", encoding="utf-8") as fh:
            fh.write("\n".join(to_close))
        try:
            out = subprocess.run(
                [sys.executable, os.path.join(HERE, "close_tabs.py"), listfile],
                capture_output=True, text=True, timeout=90,
            )
            msg = (out.stdout or out.stderr).strip()
            if out.returncode == 0:
                # trust the browser's own count, not our intent
                for tok in msg.split():
                    if tok.isdigit():
                        closed = int(tok)
                        break
            else:
                print(f"Could not close tabs: {msg}")
                kept += len(to_close)
        finally:
            if os.path.exists(listfile):
                os.remove(listfile)

    data["last_run"] = {
        "at": datetime.now().isoformat(timespec="minutes"),
        "tabs_seen": len(cls.get("tabs", [])),
        "closed": closed,
        "kept": kept,
    }

    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    # Static copy, so the dashboard still exists if the server isn't running.
    subprocess.run([sys.executable, os.path.join(HERE, "render.py")], check=True)
    print(f"Filed {filed}, closed {closed}, left {kept} open.")

    port = int(config.get("port") or PORT)
    if config.get("dashboard_opens_automatically", True):
        if ensure_server(port):
            subprocess.run(["open", f"http://localhost:{port}"])
        else:
            subprocess.run(["open", os.path.join(JDIR, "dashboard.html")])


PORT = 7777  # overridden by config["port"]


def ensure_server(port=PORT):
    """Start the dashboard server if it isn't already up. Returns True if live."""
    import socket
    import time

    def up():
        with socket.socket() as s:
            s.settimeout(0.4)
            return s.connect_ex(("127.0.0.1", port)) == 0

    if up():
        return True
    try:
        subprocess.Popen(
            [sys.executable, os.path.join(HERE, "serve.py"), "--quiet"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,  # survives this process exiting
        )
    except OSError:
        return False
    for _ in range(20):
        time.sleep(0.15)
        if up():
            return True
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: apply.py <classification.json>")
    main(sys.argv[1])
