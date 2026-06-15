
from storage.seen_urls import load_seen_urls, mark_as_seen

from scrapers.avgo_scraper import BroadcomScraper

GO = BroadcomScraper()
# ── Load seen URLs ──
try:
    seen_urls = load_seen_urls()
except Exception as e:
    # notify_error("load_seen_urls", None, e)
    print(f"CRITICAL: Could not load seen_urls — aborting. {e}")
    

# ── Step 1: scrape ──
try:
    new_releases = GO.get_new_releases(seen_urls)
except Exception as e:
    # notify_error(f"Scraper [{scraper.SOURCE_NAME}]", None, e)
    print(f"  ERROR in scraper {GO.SOURCE_NAME}: {e} — skipping")