#!/usr/bin/env python3
"""Close Chrome tabs whose URL appears in the given list.

Usage:  close_tabs.py urls.txt      (one URL per line)
        echo "https://..." | close_tabs.py -

Iterates windows and tabs in reverse so indices stay valid while closing.
"""
import json
import os
import subprocess
import sys

CONFIG = os.path.expanduser("~/.jarvis/config.json")


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def browser():
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            return json.load(fh).get("browser_app") or "Google Chrome"
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return "Google Chrome"


def close(urls):
    urls = [u.strip() for u in urls if u.strip()]
    if not urls:
        print("Nothing to close.")
        return 0

    app = browser()
    items = ", ".join(f'"{esc(u)}"' for u in urls)
    # Guarded by `is running` so closing tabs can never launch a browser.
    script = f'''
set targets to {{{items}}}
set closedCount to 0
if application "{app}" is running then
	tell application "{app}"
		repeat with wi from (count of windows) to 1 by -1
			repeat with ti from (count of tabs of window wi) to 1 by -1
				try
					set u to URL of tab ti of window wi
					if targets contains u then
						close tab ti of window wi
						set closedCount to closedCount + 1
					end if
				end try
			end repeat
		end repeat
	end tell
end if
return closedCount
'''
    try:
        proc = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=60
        )
    except FileNotFoundError:
        sys.exit("osascript not found - this script only runs on macOS.")
    except subprocess.TimeoutExpired:
        sys.exit("Chrome did not respond within 60s.")
    if proc.returncode != 0:
        sys.exit(f"Failed to close tabs: {proc.stderr.strip()}")
    n = proc.stdout.strip() or "0"
    print(f"Closed {n} tab(s).")
    return int(n)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: close_tabs.py <file-with-urls | ->")
    if sys.argv[1] == "-":
        close(sys.stdin.read().splitlines())
    else:
        with open(sys.argv[1], encoding="utf-8") as fh:
            close(fh.read().splitlines())
