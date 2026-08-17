# WLWT Nowcast Player — Python (fresh start)

Opens the WLWT Nowcast, CLICKS to start the stream, refreshes on the hour,
blocks pop-ups, recovers from crashes, and runs hidden at logon. No custom
JavaScript.

Two files (keep them together in ONE folder):
- wlwt_autoplay.py       — the player
- setup-autostart.ps1    — registers it to launch at logon

Two PowerShell windows are used below:
- [NORMAL] = Start > type PowerShell > click it
- [ADMIN]  = Start > type PowerShell > RIGHT-CLICK > Run as administrator

============================================================
STEP 1 — Install Python + Playwright (one time)
============================================================
1. Install Python 3.11+ from https://www.python.org  (tick "Add python.exe to PATH").
2. In a normal Command Prompt (Start > cmd > Enter):
       python -m pip install playwright
       python -m playwright install chromium

   NOTE: if "python" opens the Microsoft Store, install real Python from
   python.org first. See the IMPORTANT note in Step 4 about the Store alias.

============================================================
STEP 2 — Put the two files in ONE permanent folder
============================================================
Use a simple path with NO spaces, e.g.  C:\WLWT
Put wlwt_autoplay.py and setup-autostart.ps1 there. Don't move it afterward.
(Keep only ONE copy of this folder on the machine — extra copies cause extra
browser windows.)

============================================================
STEP 3 — Find the REAL Python path  [NORMAL]
============================================================
Run this (single quotes, type it rather than paste to avoid smart-quote errors):
       python -c 'import sys; print(sys.executable)'

It prints the REAL python.exe, e.g.:
       C:\Users\<you>\AppData\Local\Python\pythoncore-3.14-64\python.exe
Copy that full path — you'll use it in Step 4.

IMPORTANT: do NOT use the path from  (Get-Command python).Source  if it shows
...\Microsoft\WindowsApps\python.exe  — that is a Store "alias" stub that works
when you type it, but FAILS when a scheduled task runs it. The command above
prints the real underlying executable, which is the one to use.

============================================================
STEP 4 — Register auto-start  [ADMIN]
============================================================
Use python.exe (NOT pythonw.exe) for this Python build. The script minimizes
its own console, so no window sits in front of the stream.

       cd C:\WLWT
       powershell -ExecutionPolicy Bypass -File .\setup-autostart.ps1 -PythonwPath "PASTE_REAL_python.exe_PATH_HERE"

Type the dashes/quotes by hand if pasting causes errors. Look for:
       "Using pythonw: C:\...\python.exe"
       "Registered 'WLWT Nowcast Player' ..."

(If "Access is denied" — you're not in an elevated window. Redo as admin.)

============================================================
STEP 5 — Start it + confirm  [ADMIN]
============================================================
       Start-ScheduledTask -TaskName "WLWT Nowcast Player"
Wait ~15 seconds; Chrome opens and (after ads) the stream plays.

Check it launched cleanly:
       Get-ScheduledTaskInfo -TaskName "WLWT Nowcast Player" | Select-Object LastTaskResult
Want LastTaskResult = 0.

Confirm exactly ONE copy is running:
       Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*wlwt_autoplay.py*" } | Select-Object ProcessId | Format-List
Want exactly ONE line.

============================================================
STEP 6 — Real test
============================================================
Log off and back on (or reboot). Don't open anything. Confirm the Nowcast comes
up and plays on its own.

============================================================
Everyday commands
============================================================
Stop:    Stop-ScheduledTask  -TaskName "WLWT Nowcast Player"
Start:   Start-ScheduledTask -TaskName "WLWT Nowcast Player"
Remove:  Unregister-ScheduledTask -TaskName "WLWT Nowcast Player" -Confirm:$false
Log:     wlwt_autoplay.log  (next to the script)

============================================================
Behavior
============================================================
- Auto-starts hidden at each logon.
- Clicks to play, confirms it, then leaves the stream alone.
- Refreshes on the hour (reloads the SAME window, no new window).
- Full browser restart every 6 hours (this one DOES open a fresh window).
- Blocks pop-ups; auto-closes any stray window/tab.
- Keeps the PC awake; must be ON and LOGGED IN to show the window.

============================================================
Troubleshooting (things we hit)
============================================================
- LastTaskResult 2147942667 (0x8007000B, "incorrect format"): the task was set
  to pythonw.exe on a Python build that won't launch windowless. Fix: register
  with python.exe (Step 4).
- LastTaskResult 2147946720 (0x800710E0): task had a wrong/nonexistent Python
  path (often the WindowsApps alias or wrong username). Fix: use the real path
  from Step 3.
- "pip invalid syntax": you were at Python's >>> prompt; type exit() and run pip
  at a normal Command Prompt.
- "where python" returns nothing in PowerShell: use the Step 3 command instead.
- "cannot bind parameter Scope" / "positional parameter ... '-'": a smart quote
  or dash from pasting; retype by hand.
- "Set-Location: ... 'powershell'": two commands pasted on one line; run one per
  line (Enter after each).
- Multiple browser windows: leftover player copies from earlier launches. Kill
  them all, keep ONE folder and ONE task:
     Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object { $_.CommandLine -like "*wlwt_autoplay.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Please confirm WLWT's terms of use permit automated/unattended playback.
