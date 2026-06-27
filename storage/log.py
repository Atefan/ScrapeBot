# ─────────────────────────────────────────────
# storage/log.py
# Append-only log of every release + AI result
# ─────────────────────────────────────────────

import json
import os
from datetime import datetime, timezone
from config import RELEASES_LOG_FILE, NOTIF_LOG_FILE


# ── Releases log ──────────────────────────────

def load_releases_log():
    """Load all saved releases. Returns a list."""
    if not os.path.exists(RELEASES_LOG_FILE):
        return []
    with open(RELEASES_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def append_release(entry):
    """
    Add one release entry to the log.
    entry should be a full dict with title, url, date, body, ai, etc.
    """
    os.makedirs(os.path.dirname(RELEASES_LOG_FILE), exist_ok=True)
    log = load_releases_log()
    entry["logged_at"] = datetime.now(timezone.utc).isoformat()
    log.append(entry)
    with open(RELEASES_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print(f"  Logged: {entry.get('title', '')[:65]}")


# ── Notifications log ─────────────────────────

def load_notifications_log():
    if not os.path.exists(NOTIF_LOG_FILE):
        return []
    with open(NOTIF_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def append_notification(entry):
    """Log every notification that was sent."""
    os.makedirs(os.path.dirname(NOTIF_LOG_FILE), exist_ok=True)
    log = load_notifications_log()
    entry["sent_at"] = datetime.now(timezone.utc).isoformat()
    log.append(entry)
    with open(NOTIF_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
