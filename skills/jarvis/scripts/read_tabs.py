#!/usr/bin/env python3
"""Read every open Chrome tab via AppleScript. Prints JSON to stdout.

    read_tabs.py            -> JSON array of tabs
    read_tabs.py --debug    -> plus a diagnosis on stderr

Output: [{"window": 1, "index": 3, "url": "...", "title": "..."}, ...]

Never reports "no tabs" when it actually failed to look - if the browser is
missing, not running, or refusing automation, it says so instead.
"""
import json
import os
import subprocess
import sys

CONFIG = os.path.expanduser("~/.jarvis/config.json")

# Tabs with no future value. Filtered out, and counted so we can say so.
JUNK_PREFIXES = (
    "chrome://", "chrome-extension://", "about:", "edge://",
    "brave://", "arc://", "vivaldi://", "file:///Applications",
)

SCRIPT = '''
if application "{app}" is running then
	tell application "{app}"
		set wc to (count of windows)
		set out to "#WINDOWS" & tab & wc & linefeed
		set wi to 0
		repeat with w in windows
			set wi to wi + 1
			set ti to 0
			repeat with t in tabs of w
				set ti to ti + 1
				try
					set out to out & wi & tab & ti & tab & (URL of t) & tab & (title of t) & linefeed
				on error errMsg
					set out to out & "#ERROR" & tab & wi & tab & ti & tab & errMsg & linefeed
				end try
			end repeat
		end repeat
		return out
	end tell
else
	return "#NOTRUNNING"
end if
'''

CANDIDATES = [
    "Google Chrome", "Google Chrome Beta", "Google Chrome Canary",
    "Chromium", "Brave Browser", "Microsoft Edge", "Arc", "Vivaldi",
]


def configured_app():
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            return json.load(fh).get("browser_app") or "Google Chrome"
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return "Google Chrome"


def ask(app):
    """Returns (stdout, error_string_or_None)."""
    try:
        p = subprocess.run(
            ["osascript", "-e", SCRIPT.format(app=app)],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        return None, "osascript not found - this only runs on macOS."
    except subprocess.TimeoutExpired:
        return None, f"{app} did not respond within 30s."

    if p.returncode != 0:
        err = p.stderr.strip()
        if "-1743" in err or "Not authorized" in err:
            return None, (
                f"macOS is blocking automation of {app}.\n"
                "  Fix: System Settings > Privacy & Security > Automation,\n"
                "  find your terminal (or Claude Code) and tick Google Chrome.\n"
                "  If it isn't listed, the prompt was dismissed - run "
                "`tccutil reset AppleEvents` and try again."
            )
        if "-1728" in err or "Can't get application" in err or "-600" in err:
            return None, f"{app} isn't installed or isn't scriptable."
        return None, f"AppleScript failed for {app}: {err}"
    return p.stdout, None


def find_running_browser():
    """Which of the known browsers is actually running and has windows?"""
    found = []
    for app in CANDIDATES:
        out, err = ask(app)
        if out and not out.startswith("#NOTRUNNING"):
            wins = 0
            for line in out.split("\n"):
                if line.startswith("#WINDOWS"):
                    wins = int(line.split("\t")[1] or 0)
            found.append((app, wins))
    return found


def read_tabs(app=None, debug=False):
    app = app or configured_app()
    out, err = ask(app)

    def note(msg):
        if debug or not sys.stdout.isatty():
            print(msg, file=sys.stderr)

    if err:
        note(err)
        # Maybe she just uses a different browser.
        others = [a for a, w in find_running_browser() if a != app and w]
        if others:
            note(
                f"\n  But these ARE running with windows open: {', '.join(others)}.\n"
                f'  Set "browser_app": "{others[0]}" in ~/.jarvis/config.json.'
            )
        sys.exit(1)

    if out.startswith("#NOTRUNNING"):
        others = [a for a, w in find_running_browser() if w]
        msg = f"{app} isn't running."
        if others:
            msg += (
                f" {', '.join(others)} is, though - "
                f'set "browser_app": "{others[0]}" in ~/.jarvis/config.json.'
            )
        note(msg)
        return []

    rows, errors, windows, junk = [], [], 0, 0
    for line in out.split("\n"):
        if not line.strip():
            continue
        if line.startswith("#WINDOWS"):
            windows = int(line.split("\t")[1] or 0)
            continue
        if line.startswith("#ERROR"):
            errors.append(line)
            continue
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        w, t, url, title = parts
        url = url.strip()
        if url.startswith(JUNK_PREFIXES) or not url:
            junk += 1
            continue
        rows.append({"window": int(w), "index": int(t),
                     "url": url, "title": title.strip()})

    total = len(rows) + junk
    if debug or (not rows and not sys.stdout.isatty()):
        note(f"{app}: {windows} window(s), {total} tab(s), "
             f"{junk} blank/internal, {len(errors)} unreadable, "
             f"{len(rows)} sweepable.")
    if errors:
        note(f"  {len(errors)} tab(s) could not be read - first: {errors[0][:160]}")
    if not rows and total and junk == total:
        note("  Every open tab is a New Tab page or an internal page. "
             "Nothing to file is the correct answer here.")
    return rows


if __name__ == "__main__":
    debug = "--debug" in sys.argv
    if "--which" in sys.argv:
        for app, wins in find_running_browser():
            print(f"{app}: {wins} window(s)")
        sys.exit(0)
    print(json.dumps(read_tabs(debug=debug), indent=2, ensure_ascii=False))
