# ─────────────────────────────────────────────
# storage/seen_urls.py
# Tracks all URLs ever processed — used for deduplication
# ─────────────────────────────────────────────

import json
import os
from config import SEEN_URLS_FILE


def load_seen_urls():
    """Load the set of already-processed URLs from disk."""
    if not os.path.exists(SEEN_URLS_FILE):
        return set()
    with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen_urls(seen_urls):
    """Persist the full set of seen URLs to disk."""
    os.makedirs(os.path.dirname(SEEN_URLS_FILE), exist_ok=True)
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_urls), f, indent=2)


def mark_as_seen(url, seen_urls):
    """Add a URL to the seen set and save immediately."""
    seen_urls.add(url)
    save_seen_urls(seen_urls)


def is_seen(url, seen_urls):
    return url in seen_urls
