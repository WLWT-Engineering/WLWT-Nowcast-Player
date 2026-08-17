WLWT Nowcast Auto-Play — Python Player

Keeps the WLWT News 5 Nowcast livestream playing on a Windows PC, unattended, starting automatically at logon. Built with Python + Playwright. Uses no custom JavaScript.

What it does

The WLWT page never truly autoplays — it needs a real click to start the stream. This script does that reliably, the way a person would, and then keeps it running:

Clicks to play, then confirms it's playing — and re-clicks if it isn't. Because it verifies instead of hoping, it avoids the on-again/off-again behavior of the old "launch flag" approach.
Refreshes on the hour — reloads the page at the top of each clock hour (9:00, 10:00, …) and restarts playback. Between refreshes it leaves the stream alone (no stray mid-stream clicks).
Blocks pop-ups — prevents the page from opening new windows/tabs, auto-closes any that appear, and suppresses notification prompts.
Self-recovers — if the browser crashes, it relaunches within ~10 seconds, and it does a full browser restart every 6 hours for long-run stability.
Keeps the PC awake so the machine doesn't sleep and stop the stream.
Runs hidden at logon — no window sitting in front of the stream; it also minimizes its own console if you ever run it by hand.
Logs everything to wlwt_autoplay.log (opens, clicks, refreshes, pop-up closes, restarts) so you can see exactly what it did.

Because it always ensures a stream is playing, it naturally covers any newscast — scheduled or breaking — without a fixed timetable.

No custom JavaScript: all page interaction uses Playwright's native Python actions (clicks, role/text locators, visibility checks). It never injects a script. WLWT's own site scripts run as they would in any browser.

Files
wlwt_autoplay.py — the player.
setup-autostart.ps1 — registers it to launch hidden at logon.
wlwt_profile/ and wlwt_autoplay.log — created automatically next to the script the first time it runs.
Install

Two PowerShell windows are referenced below:

[NORMAL] = Start → type PowerShell → click it
[ADMIN] = Start → type PowerShell → right-click → Run as administrator
1. Install Python + Playwright (one time)
Install Python 3.11+ from https://www.python.org (tick "Add python.exe to PATH" on the first installer screen).
In a normal Command Prompt (Start → cmd → Enter):
   python -m pip install playwright
   python -m playwright install chromium
2. Put the files in one permanent folder

Use a simple path with no spaces, e.g. C:\WLWT. Put wlwt_autoplay.py and setup-autostart.ps1 there. Don't move the folder afterward — the scheduled task points at this location.

3. Find the REAL Python path [NORMAL]
python -c "import sys; print(sys.executable)"

This prints the real python.exe, e.g. C:\Users\<you>\AppData\Local\Python\pythoncore-3.14-64\python.exe. Copy it — you'll use it in the next step.

Important: do NOT use the path from (Get-Command python).Source if it shows ...\Microsoft\WindowsApps\python.exe — that's a Microsoft Store "alias" stub that works when you type it but fails when a scheduled task runs it. The command above prints the real executable, which is the one to use.

4. Register auto-start [ADMIN]

Registering a scheduled task needs an elevated window. From your folder:

cd C:\WLWT
powershell -ExecutionPolicy Bypass -File .\setup-autostart.ps1 -PythonwPath "PASTE_REAL_python.exe_PATH_HERE"

Look for Using pythonw: ... and Registered 'WLWT Nowcast Player' ....

Note: on newer Python builds, use the python.exe path here (not pythonw.exe) — some builds fail to launch windowless under Task Scheduler (error 0x8007000B). The script minimizes its own console, so nothing sits in front of the stream either way.

5. Start it and test [ADMIN]
Start-ScheduledTask -TaskName "WLWT Nowcast Player"

A Chrome window opens and, after the stream's pre-roll ads, the live feed plays.

Confirm it launched cleanly:

Get-ScheduledTaskInfo -TaskName "WLWT Nowcast Player" | Select-Object LastTaskResult

0 = good. 267009 also = fine (means "currently running").

6. Real test

Log off and back on (or reboot). Don't open anything. The Nowcast should come up and play on its own.

Everyday commands
Stop:    Stop-ScheduledTask  -TaskName "WLWT Nowcast Player"
Start:   Start-ScheduledTask -TaskName "WLWT Nowcast Player"
Remove:  Unregister-ScheduledTask -TaskName "WLWT Nowcast Player" -Confirm:$false
To pause a hand-run copy: click its window and press Ctrl+C.
Check what it's been doing: open wlwt_autoplay.log.
In normal use it auto-starts once at logon — only Start-ScheduledTask if it isn't already running (starting a second copy = a second browser window).
Tuning (top of wlwt_autoplay.py)
REFRESH_ON_THE_HOUR = True — refresh at the top of each clock hour. Set False to use RELOAD_MINUTES (every N minutes from start) instead.
RELOAD_MINUTES = 60 — interval used only when REFRESH_ON_THE_HOUR is False.
CHECK_SECONDS = 20 — how often it checks the clock / browser health.
RESTART_HOURS = 6 — full browser restart interval.
ZOOM = 0.6 — page zoom (helps center the video).
PLAY_RE / PAUSE_RE / CONSENT_RE — text matchers for the play/pause/ consent controls. If the log shows it clicking the wrong thing, adjust PLAY_RE.
Troubleshooting
"pip invalid syntax" — you were at Python's >>> prompt. Type exit(), then run pip at a normal Command Prompt.
where python returns nothing — in PowerShell use the Step 3 command (python -c "import sys; print(sys.executable)") instead.
"Access is denied" registering the task — run PowerShell as Administrator.
Task result 2147946720 (0x800710E0) — the task has a wrong/missing Python path (often the WindowsApps alias). Re-register with the real path (Step 3–4).
Task result 2147942667 (0x8007000B, "incorrect format") — the task was set to pythonw.exe on a build that won't launch windowless. Re-register with the python.exe path.
Two browser windows — a leftover copy is running. Stop the task, then:
  Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object { $_.CommandLine -like "*wlwt_autoplay.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

then start the task once.

Notes & limits
The PC must be on and logged in for the browser to show.
The pre-roll/in-stream ads are part of WLWT's feed and can't be removed.
Please confirm WLWT's terms of use permit automated / unattended playback.
