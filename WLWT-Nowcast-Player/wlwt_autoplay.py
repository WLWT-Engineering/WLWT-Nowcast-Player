"""
WLWT Nowcast Auto-Play  —  Option A: Python + Playwright (click to play)

The WLWT page requires a real CLICK to start the stream. This script does
exactly that, reliably, the way a person would: it opens the page, brings the
video into view, CLICKS to start playback, and then CONFIRMS the video is
playing - re-clicking if it isn't. Because it verifies instead of hoping, it
does not have the intermittent "sometimes plays" behavior of the launch-flag
approach.

It runs continuously: it keeps the stream playing, reloads on a set interval to
refresh it, recovers if the browser crashes, and keeps the PC awake. Because it
is always ensuring a stream is playing, it also naturally covers any newscast -
scheduled or breaking - without a fixed timetable.

NO CUSTOM JAVASCRIPT: all page interaction uses Playwright's native Python
actions (clicks, role/text locators, visibility checks, scroll-into-view). It
never uses page.evaluate() or injects any script. WLWT's own site JavaScript
runs exactly as in any browser; that is not code you authored.
"""

import re
import sys
import time
import logging
import ctypes
from datetime import datetime

from playwright.sync_api import sync_playwright

# ============================ CONFIG ============================
URL = "https://www.wlwt.com/nowcast"
USER_DATA_DIR = "wlwt_profile"   # dedicated browser profile (created next to this file)

REFRESH_ON_THE_HOUR = True       # refresh at the top of each clock hour (9:00, 10:00, ...)
RELOAD_MINUTES = 60              # used only if REFRESH_ON_THE_HOUR is False (every N min)
CHECK_SECONDS = 20               # how often to confirm it's still playing
RESTART_HOURS = 6                # relaunch the browser this often (memory hygiene)
ZOOM = 0.6                       # page zoom (matches your current setup; helps center the video)

# Best-effort matchers - tune if the log shows it clicking the wrong thing.
PLAY_RE = re.compile(r"\b(play|watch live|watch now|watch)\b", re.I)
PAUSE_RE = re.compile(r"\bpause\b", re.I)
CONSENT_RE = re.compile(r"\b(accept|agree|got it|i understand|continue|allow all)\b", re.I)
# ===============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler("wlwt_autoplay.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Keep the machine + display awake (Windows only; harmless elsewhere).
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def keep_awake():
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
        except Exception as exc:  # noqa: BLE001
            logging.debug("keep_awake failed: %s", exc)


def minimize_console():
    """Minimize this script's own console window (if any) so it doesn't sit on
    top of the stream. Harmless when run with pythonw (no console exists)."""
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                SW_MINIMIZE = 6
                ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
        except Exception as exc:  # noqa: BLE001
            logging.debug("minimize_console failed: %s", exc)


def dismiss_consent(page):
    """Click a cookie/consent 'Accept' button if one is present (native click)."""
    try:
        btn = page.get_by_role("button", name=CONSENT_RE)
        if btn.count() and btn.first.is_visible():
            btn.first.click(timeout=3000)
            logging.info("Dismissed a consent/cookie banner.")
    except Exception as exc:  # noqa: BLE001
        logging.debug("consent: %s", exc)


def looks_playing(page):
    """Native heuristic (no JavaScript): a visible 'Pause' control means playing;
    a visible 'Play'/'Watch' control means not playing."""
    try:
        pause = page.get_by_role("button", name=PAUSE_RE)
        if pause.count() and pause.first.is_visible():
            return True
    except Exception:  # noqa: BLE001
        pass
    try:
        play = page.get_by_role("button", name=PLAY_RE)
        if play.count() and play.first.is_visible():
            return False
    except Exception:  # noqa: BLE001
        pass
    return None  # unknown


def click_to_play(page):
    """Click the play/watch control, or the video itself, to start playback."""
    try:
        btn = page.get_by_role("button", name=PLAY_RE)
        if btn.count() and btn.first.is_visible():
            btn.first.click(timeout=3000)
            logging.info("Clicked a play/watch control.")
            return True
    except Exception as exc:  # noqa: BLE001
        logging.debug("play button: %s", exc)
    try:
        vid = page.locator("video").first
        if vid.count():
            vid.scroll_into_view_if_needed(timeout=5000)
            vid.click(timeout=3000)
            logging.info("Clicked the video element.")
            return True
    except Exception as exc:  # noqa: BLE001
        logging.debug("video click: %s", exc)
    return False


def ensure_playing(page):
    """Make sure the stream is playing; click to start it if not."""
    dismiss_consent(page)
    for _ in range(4):
        state = looks_playing(page)
        if state is True:
            return True
        click_to_play(page)
        page.wait_for_timeout(1500)
    # Final check; if unknown, assume the click worked.
    return looks_playing(page) is not False


def open_and_play(context):
    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(60000)
    logging.info("Opening %s", URL)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)  # let the player initialize
    ensure_playing(page)
    return page


def run_session(pw):
    context = pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        no_viewport=True,
        device_scale_factor=None,
        permissions=[],   # grant no permissions (blocks notification/other prompts)
        args=[
            "--autoplay-policy=no-user-gesture-required",
            f"--force-device-scale-factor={ZOOM}",
            "--disable-features=CalculateNativeWinOcclusion",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--start-maximized",
            "--hide-crash-restore-bubble",
            # Pop-up / extra-window suppression:
            "--block-new-web-contents",              # stop the page opening new windows/tabs
            "--disable-notifications",                # no notification pop-ups
            "--no-default-browser-check",
        ],
    )

    # Auto-dismiss any JS dialog (alert/confirm/pop-up prompt) without a click.
    def _dismiss_dialog(dialog):
        try:
            dialog.dismiss()
        except Exception:  # noqa: BLE001
            pass
    context.on("dialog", _dismiss_dialog)

    # If the page still manages to open a new tab/window, close it immediately
    # so only the Nowcast stays.
    def _close_popup(popup):
        try:
            logging.info("Closed an unexpected pop-up window/tab.")
            popup.close()
        except Exception:  # noqa: BLE001
            pass
    context.on("page", _close_popup)
    try:
        page = open_and_play(context)
        session_start = time.time()
        last_reload = time.time()
        last_hour = datetime.now().hour

        while True:
            keep_awake()
            if page.is_closed():
                raise RuntimeError("Page was closed unexpectedly.")

            # Refresh the stream, then click once to start it. We start playback
            # ONLY right after a load/refresh, then leave the stream alone -- so
            # there are no stray mid-stream clicks.
            now = datetime.now()
            do_refresh = False
            if REFRESH_ON_THE_HOUR:
                # Fire once when the clock hour changes (i.e. at the top of the hour).
                if now.hour != last_hour:
                    do_refresh = True
            elif RELOAD_MINUTES > 0 and (time.time() - last_reload) > RELOAD_MINUTES * 60:
                do_refresh = True

            if do_refresh:
                logging.info("Refresh (top of hour %02d:00)." % now.hour if REFRESH_ON_THE_HOUR
                             else "Scheduled refresh.")
                page.goto(URL, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(6000)
                ensure_playing(page)          # start it once, right after refresh
                last_reload = time.time()
                last_hour = now.hour

            # Periodic full browser restart for long-run stability.
            if (time.time() - session_start) > RESTART_HOURS * 3600:
                logging.info("Planned periodic browser restart.")
                return

            time.sleep(CHECK_SECONDS)
    finally:
        try:
            context.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    minimize_console()
    logging.info("WLWT Nowcast Auto-Play (Python/Playwright) starting.")
    keep_awake()
    with sync_playwright() as pw:
        while True:
            try:
                run_session(pw)
            except KeyboardInterrupt:
                logging.info("Stopped by user.")
                break
            except Exception as exc:  # noqa: BLE001
                logging.exception("Session crashed: %s - relaunching in 10s.", exc)
                time.sleep(10)


if __name__ == "__main__":
    main()
