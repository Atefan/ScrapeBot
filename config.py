# ─────────────────────────────────────────────
# config.py — all settings in one place
# ─────────────────────────────────────────────

# Anthropic API key — set this as an environment variable, never hardcode
import os
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Telegram — set via environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Shared HTTP headers for all scrapers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# Data file paths
SEEN_URLS_FILE      = "data/seen_urls.json"
RELEASES_LOG_FILE   = "data/releases_log.json"
NOTIF_LOG_FILE      = "data/notifications_log.json"

# Scraper settings
REQUEST_DELAY = 1   # seconds between requests — be polite


# from storage.seen_urls import load_seen_urls, mark_as_seen

# from scrapers.aapl_scraper import AppleScraper
# from scrapers.avgo_scraper import BroadcomScraper

# GO = BroadcomScraper()
# # ── Load seen URLs ──
# try:
#     seen_urls = load_seen_urls()
# except Exception as e:
#     # notify_error("load_seen_urls", None, e)
#     print(f"CRITICAL: Could not load seen_urls — aborting. {e}")
    

# # ── Step 1: scrape ──
# try:
#     new_releases = GO.get_new_releases(seen_urls)
# except Exception as e:
#     # notify_error(f"Scraper [{scraper.SOURCE_NAME}]", None, e)
#     print(f"  ERROR in scraper {GO.SOURCE_NAME}: {e} — skipping")