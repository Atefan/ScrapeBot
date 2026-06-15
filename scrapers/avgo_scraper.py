# ─────────────────────────────────────────────
# scrapers/avgo_scraper.py
# Broadcom (AVGO) specific scraper
# HTML structure confirmed by diagnostic scripts June 2026
#
# Listing: https://www.globenewswire.com/search/keyword/broadcom?type=news&pageSize=50
# Filter:  <li> elements that contain a "Source: Broadcom Inc." anchor
#          href="/en/search/organization/Broadcom%2520Inc§..."
# Pagination: ?page=N, "Next Page" text signals more pages exist
#
# Example article (exemplary deal press release):
#   /news-release/2026/04/14/3273998/19933/en/
#   Broadcom-Announces-Extended-Partnership-with-Meta-...MTIA.html
#
# Article body: <section class="main-body-container"> with <p>, <li>
# Date: wire-timestamp element or text in <li> — "June 01, 2026 16:05 ET|Source:..."
# ─────────────────────────────────────────────

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper

GLOBENEWSWIRE_BASE = "https://www.globenewswire.com"
BASE_LISTING       = "https://www.globenewswire.com/search/keyword/broadcom?type=news&pageSize=50"

# Normal cron run: check page 1 only (50 results covers ~30 min of news easily)
# First run (empty seen_urls): paginate deeper to backfill history
MAX_PAGES_NORMAL   = 1
MAX_PAGES_BACKFILL = 5

# ── Noise filter: skip earnings and admin releases ──
SKIP_TITLE_FRAGMENTS = [
    "financial results",
    "quarterly dividend",
    "to report",
    "to host",
    "annual meeting",
]


def _parse_gnw_date(raw: str) -> str:
    """
    Parse GlobeNewswire date string to ISO YYYY-MM-DD.
    Input:  "May 19, 2026 03:01 ET|Source:Broadcom Inc."
            "June 01, 2026 16:05 ET | Source: Broadcom Inc."
    Output: "2026-05-19"
    """
    if not raw:
        return ""
    date_part = raw.split("|")[0].strip()           # "May 19, 2026 03:01 ET"
    date_part = " ".join(date_part.split()[:3])     # "May 19, 2026"
    date_part = date_part.rstrip(",")
    try:
        return datetime.strptime(date_part, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return raw[:10]


class BroadcomScraper(BaseScraper):

    SOURCE_NAME = "Broadcom"
    BASE_URL    = GLOBENEWSWIRE_BASE
    NEWS_URL    = BASE_LISTING

    # ── fetch_main_page not used — pagination handled in get_new_releases ──
    def fetch_main_page(self):
        return None

    # ── Parse one listing page, return (results, has_next) ──
    def _parse_page(self, page_num: int) -> tuple:
        """
        GlobeNewswire search result HTML structure (confirmed June 2026):

          <li class="row">
            <span class="wire-timestamp">May 19, 2026 03:01 ET|Source:Broadcom Inc.</span>
            <div class="mainLink">
              <a href="/news-release/.../19933/en/slug.html">Title</a>
            </div>
            <a href="/en/search/organization/Broadcom%2520Inc§...">Broadcom Inc.</a>
          </li>

        Strategy: find all <a> tags whose href contains "Broadcom" (the source
        org link). Walk up to the parent <li> and extract the title + date.
        """
        url = f"{BASE_LISTING}&page={page_num}" if page_num > 1 else BASE_LISTING
        print(f"  GET {url}")

        from config import HEADERS
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup     = BeautifulSoup(resp.text, "html.parser")
        has_next = "Next Page" in resp.text
        results  = []
        seen     = set()

        # Each Broadcom article has a "Source: Broadcom Inc." org link
        for org_a in soup.find_all("a", href=re.compile(r"Broadcom", re.IGNORECASE)):
            parent = org_a.find_parent("li")
            if not parent:
                continue

            # Title anchor — links to the news-release page
            title_a = parent.find("a", href=re.compile(r"/news-release/"))
            if not title_a:
                continue

            href  = title_a.get("href", "")
            title = title_a.get_text(strip=True)
            if not href or not title:
                continue
            if href.startswith("/"):
                href = GLOBENEWSWIRE_BASE + href
            if href in seen:
                continue
            seen.add(href)

            # Noise filter
            if any(frag in title.lower() for frag in SKIP_TITLE_FRAGMENTS):
                continue

            # Date — prefer wire-timestamp span, fall back to li text
            date    = ""
            date_el = parent.select_one(".wire-timestamp, time, [class*='date']")
            if date_el:
                date = _parse_gnw_date(date_el.get_text(strip=True))
            if not date:
                li_text = parent.get_text(" ", strip=True)
                m = re.search(
                    r'(January|February|March|April|May|June|July|August|'
                    r'September|October|November|December)\s+\d{1,2},\s+\d{4}',
                    li_text
                )
                if m:
                    date = _parse_gnw_date(m.group(0))

            results.append({"title": title, "url": href, "date": date})

        return results, has_next

    def parse_press_releases(self, soup):
        return []  # not used — pagination handled in get_new_releases

    # ── Fetch full article body ──
    def fetch_article_body(self, url):
        """
        GlobeNewswire article page structure:

          <meta name="DC.date.issued" content="2026-04-14">

          <section class="main-body-container">
            <p>PALO ALTO... (GLOBE NEWSWIRE)...</p>
            <ul><li>...</li></ul>
            <p>About Broadcom</p>   ← stop here
          </section>
        """
        soup = self.fetch_page(url)

        # ISO date from DC meta (most reliable on GlobeNewswire)
        iso_date = ""
        dc_date  = soup.find("meta", attrs={"name": "DC.date.issued"})
        if dc_date:
            iso_date = (dc_date.get("content", "") or "")[:10]
        if not iso_date:
            pub_meta = soup.find("meta", property="article:published_time")
            if pub_meta:
                iso_date = (pub_meta.get("content", "") or "")[:10]

        body = soup.select_one(
            "section.main-body-container, div.main-body-container, "
            "div[class*='article-body'], div[class*='press-release-body']"
        )
        if not body:
            body = soup.find("article") or soup.find("main")

        if not body:
            print("  WARNING: no article body found")
            return "", iso_date

        for tag in body.find_all(["script", "style", "img", "figure",
                                   "nav", "aside", "header", "footer"]):
            tag.decompose()

        paragraphs = []
        for el in body.find_all(["p", "li", "h2", "h3", "h4"]):
            text = el.get_text(strip=True)
            if not text:
                continue
            if text.startswith("About Broadcom") or text.startswith("Cautionary Note"):
                break
            paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text, iso_date

    # ── Full pipeline ──
    def get_new_releases(self, seen_urls):
        from config import REQUEST_DELAY

        max_pages   = MAX_PAGES_BACKFILL if not seen_urls else MAX_PAGES_NORMAL
        all_releases = []
        seen_in_run  = set()

        for page in range(1, max_pages + 1):
            time.sleep(REQUEST_DELAY)
            try:
                releases, has_next = self._parse_page(page)
            except Exception as e:
                print(f"  ERROR fetching page {page}: {e}")
                break

            for r in releases:
                if r["url"] not in seen_in_run:
                    seen_in_run.add(r["url"])
                    all_releases.append(r)

            if not has_next:
                break

        print(f"  Found {len(all_releases)} total Broadcom release(s) across pages")

        new = []
        for release in all_releases:
            if release["url"] in seen_urls:
                print(f"  SKIP: {release['title'][:65]}")
                continue

            print(f"  NEW:  {release['title'][:65]}")
            time.sleep(REQUEST_DELAY)

            body, iso_date = self.fetch_article_body(release["url"])
            new.append({
                "source": self.SOURCE_NAME,
                "title":  release["title"],
                "url":    release["url"],
                "date":   iso_date or release["date"],
                "body":   body,
            })

        print(f"[{self.SOURCE_NAME}] {len(new)} new release(s) found")
        return new
