# ─────────────────────────────────────────────
# scrapers/aapl_scraper.py
# Apple-specific scraper
# HTML structure confirmed by inspection June 2026
#
# WHY RSS: apple.com/newsroom listing page is JS-rendered — article cards
# are injected client-side, invisible to requests+BeautifulSoup.
# The official RSS feed at apple.com/newsroom/rss-feed.rss is pure
# server-rendered XML and contains the same articles.
#
# Listing (RSS): https://www.apple.com/newsroom/rss-feed.rss
# Filter:        only <category> = "Press Release"
#                (excludes Apple Stories, Apple Services feature pieces)
#
# Example article (exemplary deal press release):
#   https://www.apple.com/newsroom/2025/02/apple-will-spend-more-than-500-billion-usd-in-the-us-over-the-next-four-years/
#   Apple $500B+ US investment commitment
#
# Article body: <div class="article-body"> with <p>, <li>, <h2>, <h3>
# Date:         <pubDate> in RSS (RFC 2822) → ISO YYYY-MM-DD
# ─────────────────────────────────────────────

import xml.etree.ElementTree as ET
import time

import requests
from scrapers.base_scraper import BaseScraper

# ── Noise filter: skip pure admin/earnings releases ──
SKIP_TITLE_FRAGMENTS = [
    "apple reports",           # quarterly earnings
    "apple announces results",
]


class AppleScraper(BaseScraper):

    SOURCE_NAME = "Apple"
    BASE_URL    = "https://www.apple.com"
    NEWS_URL    = "https://www.apple.com/newsroom/rss-feed.rss"

    # ── Override fetch_main_page to return raw RSS text ──
    def fetch_main_page(self):
        """Returns raw RSS XML string instead of BeautifulSoup."""
        from config import HEADERS
        print(f"\n[{self.SOURCE_NAME}] Fetching RSS feed: {self.NEWS_URL}")
        resp = requests.get(self.NEWS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text

    # ── Parse press releases from Atom feed ──
    def parse_press_releases(self, rss_text):
        """
        Apple Newsroom uses ATOM format, not RSS.

        Atom <entry> structure:
          <entry>
            <title><![CDATA[Apple adds new partners...]]></title>
            <link href="https://www.apple.com/newsroom/2026/03/.../"/>
            <id><![CDATA[https://www.apple.com/newsroom/2026/03/.../]]></id>
            <author><name><![CDATA[Apple Newsroom]]></name></author>
            <content><![CDATA[summary text...]]></content>
          </entry>

        NO <category> tag in this feed — we filter by URL path instead:
          /newsroom/YYYY/MM/ paths that are NOT apple-arcade, apple-stories,
          apple-tv, app-store-games, etc.
        """
        results = []
        seen    = set()

        try:
            import re
            # Strip namespaces so ET can parse cleanly
            rss_clean = re.sub(r'\s+xmlns[^=]*="[^"]*"', "", rss_text)
            # Also strip namespace prefixes on tags e.g. <atom:link> → <link>
            rss_clean = re.sub(r'<(/?)[\w]+:([\w]+)', r'<\1\2', rss_clean)
            root = ET.fromstring(rss_clean)
        except ET.ParseError as e:
            print(f"  ERROR: failed to parse Atom XML: {e}")
            return results

        # Atom uses <entry> not <item>
        entries = root.findall(".//entry")
        if not entries:
            print("  ERROR: no <entry> elements found — check feed format")
            return results

        for entry in entries:
            # Title — wrapped in CDATA
            title_el = entry.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""

            # Link — Atom uses <link href="..."/> not <link>text</link>
            link_el = entry.find("link")
            url = ""
            if link_el is not None:
                url = link_el.get("href", "").strip()

            if not url or not title:
                continue
            if url in seen:
                continue

            # ── Filter: only keep investment/company-level press releases ──
            # Exclude known noise path fragments
            skip_fragments = [
                "apple-arcade", "apple-tv", "apple-music", "app-store-games",
                "apple-watch-app", "iphone-", "ipad-", "mac-", "airpods",
                "apple-stories", "apple-vision",
            ]
            url_lower = url.lower()
            if any(frag in url_lower for frag in skip_fragments):
                continue

            # Noise filter on title
            if any(frag in title.lower() for frag in SKIP_TITLE_FRAGMENTS):
                continue

            seen.add(url)

            # Date — Atom uses <updated> or <published>
            date = ""
            for date_tag in ["published", "updated"]:
                date_el = entry.find(date_tag)
                if date_el is not None and date_el.text:
                    date = date_el.text.strip()[:10]  # "2026-03-26T..." → "2026-03-26"
                    break

            results.append({
                "title": title,
                "url":   url,
                "date":  date,
            })

        print(f"  Found {len(results)} press release(s) in Atom feed")
        return results

    # ── Fetch full article body ──
    def fetch_article_body(self, url):
        """
        Apple Newsroom article page structure:

          <meta property="article:published_time" content="2025-02-17T...">

          <div class="article-body">       ← primary container
            <p>...</p>
            <ul><li>...</li></ul>
            <h2>...</h2>
          </div>

        Fallback chain:
          div.article-body → div[class*='article'] → main → body
        """
        soup = self.fetch_page(url)

        # ISO date from og meta
        published_meta = soup.find("meta", property="article:published_time")
        iso_date = ""
        if published_meta:
            iso_date = (published_meta.get("content", "") or "")[:10]

        body = soup.find("div", class_="article-body")
        if not body:
            body = soup.select_one("div[class*='article-body'], div[class*='ArticleBody']")
        if not body:
            body = soup.find("main")

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
            # Stop at boilerplate
            if text.startswith("Apple revolutionized") or text.startswith("Press Contacts"):
                break
            paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text, iso_date

    # ── Override get_new_releases to handle RSS flow + iso_date ──
    def get_new_releases(self, seen_urls):
        from config import REQUEST_DELAY

        rss_text = self.fetch_main_page()
        releases = self.parse_press_releases(rss_text)
        new      = []

        for release in releases:
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
