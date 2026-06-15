# ─────────────────────────────────────────────
# scrapers/google_scraper.py
# Google (Alphabet) specific scraper
# HTML structure confirmed by inspection June 2026
#
# WHY RSS: blog.google listing pages are JS-rendered — article cards are
# injected client-side and invisible to requests+BeautifulSoup.
# The RSS feed is pure server-rendered XML and contains the same articles.
#
# Listing (RSS): https://blog.google/rss/
# Filter:        only items whose <category> contains "Company News" or
#                whose URL path contains /company-news/ or
#                /innovation-and-ai/infrastructure-and-cloud/
#
# Example article (exemplary deal press release):
#   https://blog.google/intl/en-in/company-news/technology/sundar-pichai-io-2026/
#   Alphabet $190B capex + infrastructure investment announcements
#
# Article body: <div class="article-body"> or <div class="rich-text">
# Date:         <pubDate> in RSS (RFC 2822) or og meta article:published_time
# ─────────────────────────────────────────────

import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
import time

from scrapers.base_scraper import BaseScraper

# ── URL path fragments that indicate investor-relevant content ──
# blog.google RSS covers all Google blog posts; filter to company/infra only.
INVESTMENT_PATHS = [
    "/company-news/",
    "/innovation-and-ai/infrastructure-and-cloud/",
]

# ── Category strings from RSS <category> tags that signal relevance ──
INVESTMENT_CATEGORIES = {
    "company news",
    "infrastructure & cloud",
    "infrastructure and cloud",
    "google cloud",
    "outreach and initiatives",
    "outreach & initiatives",
    "creating opportunity",
    "public policy",
}

# ── Title fragments to skip (noise in company-news category) ──
SKIP_TITLE_FRAGMENTS = [
    "doodle",
    "life at google",
    "year in search",
    "google i/o keynote recap",
]


def _parse_rfc2822_date(raw: str) -> str:
    """
    Parse RSS pubDate (RFC 2822) to ISO YYYY-MM-DD.
    Input:  "Thu, 21 May 2026 11:00:07 +0000"
    Output: "2026-05-21"
    """
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).strftime("%Y-%m-%d")
    except Exception:
        return raw[:10] if len(raw) >= 10 else raw


class GoogleScraper(BaseScraper):

    SOURCE_NAME = "Google"
    BASE_URL    = "https://blog.google"
    NEWS_URL    = "https://blog.google/rss/"  # server-rendered XML

    # ── Override fetch_main_page to return raw RSS text ──
    def fetch_main_page(self):
        """
        Returns the raw RSS XML text rather than a BeautifulSoup object.
        parse_press_releases() handles the XML parsing.
        """
        import requests
        from config import HEADERS
        print(f"\n[{self.SOURCE_NAME}] Fetching RSS feed: {self.NEWS_URL}")
        resp = requests.get(self.NEWS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text  # raw XML string

    # ── Parse press releases from RSS feed ──
    def parse_press_releases(self, rss_text):
        """
        RSS <item> structure:
          <item>
            <title>Google Invests $15B in Missouri Data Center</title>
            <link>https://blog.google/company-news/.../</link>
            <pubDate>Thu, 22 May 2026 14:00:00 +0000</pubDate>
            <category>Company News</category>
            <category>Infrastructure & Cloud</category>
            <description>...</description>
          </item>

        Filter: keep items whose link contains an INVESTMENT_PATH
        OR whose category matches INVESTMENT_CATEGORIES.
        """
        results = []
        seen    = set()

        try:
            root = ET.fromstring(rss_text)
        except ET.ParseError as e:
            print(f"  ERROR: failed to parse RSS XML: {e}")
            return results

        # RSS: <rss><channel><item>...</item></channel></rss>
        channel = root.find("channel")
        if channel is None:
            print("  ERROR: no <channel> found in RSS")
            return results

        items = channel.findall("item")

        for item in items:
            link  = (item.findtext("link") or "").strip()
            title = (item.findtext("title") or "").strip()
            pub   = (item.findtext("pubDate") or "").strip()

            if not link or not title:
                continue
            if link in seen:
                continue

            # Category tags (there can be multiple)
            categories = [
                c.text.strip().lower()
                for c in item.findall("category")
                if c.text
            ]

            # ── Filter: path-based OR category-based ──
            path_match     = any(p in link for p in INVESTMENT_PATHS)
            category_match = bool(INVESTMENT_CATEGORIES & set(categories))

            if not path_match and not category_match:
                continue

            # Skip noise by title
            title_lower = title.lower()
            if any(frag in title_lower for frag in SKIP_TITLE_FRAGMENTS):
                continue

            seen.add(link)
            results.append({
                "title": title,
                "url":   link,
                "date":  _parse_rfc2822_date(pub),  # → "2026-05-22"
            })

        print(f"  Found {len(results)} press release(s) in RSS feed")
        return results

    # ── Fetch full article body ──
    def fetch_article_body(self, url):
        """
        blog.google article page structure:

          <meta property="article:published_time" content="2026-05-21T11:00:07+00:00">

          <div class="article-body">        ← primary container
            <div class="rich-text">
              <p>...</p>
              <h2>...</h2>
              <ul><li>...</li></ul>
            </div>
          </div>

        Fallback chain:
          div.article-body → div.rich-text → article → main
        """
        soup = self.fetch_page(url)

        # ISO date from og meta (most reliable)
        published_meta = soup.find("meta", property="article:published_time")
        iso_date = ""
        if published_meta:
            content = published_meta.get("content", "")
            iso_date = content[:10]  # "2026-05-21T11:00:07+00:00" → "2026-05-21"

        # Body selectors
        body = soup.select_one("div.article-body, div[class*='article-body']")
        if not body:
            body = soup.select_one("div.rich-text, div[class*='rich-text']")
        if not body:
            body = soup.find("article")
        if not body:
            body = soup.find("main")

        if not body:
            print("  WARNING: no article body found")
            return "", iso_date

        # Strip noise
        for tag in body.find_all(["script", "style", "img", "figure",
                                   "nav", "aside", "header", "footer"]):
            tag.decompose()

        paragraphs = []
        for element in body.find_all(["p", "li", "h2", "h3", "h4"]):
            text = element.get_text(strip=True)
            if text:
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text, iso_date

    # ── Override get_new_releases to handle RSS flow + iso_date ──
    def get_new_releases(self, seen_urls):
        from config import REQUEST_DELAY

        rss_text = self.fetch_main_page()    # raw XML string
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
                "date":   iso_date or release["date"],  # og meta preferred
                "body":   body,
            })

        print(f"[{self.SOURCE_NAME}] {len(new)} new release(s) found")
        return new