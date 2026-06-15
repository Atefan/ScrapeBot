# ─────────────────────────────────────────────
# Tester.py — quick sanity check for scrapers
# ─────────────────────────────────────────────

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from scrapers.globenewswire_scraper import GlobeNewswireScraper

def test_globenewswire():
    print("\n" + "="*55)
    print("  Testing GlobeNewswireScraper")
    print("="*55)

    scraper = GlobeNewswireScraper()

    # Pass empty seen_urls so nothing is skipped
    releases = scraper.get_new_releases(seen_urls=set())

    if not releases:
        print("\n  ⚠️  No releases found — either no watchlist hits right now or something is broken.")
        return

    print(f"\n  ✅ Found {len(releases)} release(s). Showing first:\n")

    r = releases[0]
    print(f"  Source  : {r.get('source')}")
    print(f"  Title   : {r.get('title')}")
    print(f"  URL     : {r.get('url')}")
    print(f"  Date    : {r.get('date')}")
    print(f"  Body    : {len(r.get('body', ''))} chars")
    print(f"  Preview : {r.get('body', '')[:300]}")
    print("\n" + "="*55)


if __name__ == "__main__":
    test_globenewswire()