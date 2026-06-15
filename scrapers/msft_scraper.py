# ─────────────────────────────────────────────
# scrapers/msft_scraper.py
# Microsoft-specific scraper
# HTML structure confirmed by inspection June 2026
#
# Listing page:  https://news.microsoft.com/source/tag/press-releases/
# Example article (exemplary deal press release):
#   https://news.microsoft.com/source/2026/05/21/ey-and-microsoft-announce-global-initiative
#   -to-help-clients-scale-ai-enterprisewide-value-creation-and-move-beyond-experimentation/
#
# Platform: WordPress — server-rendered, no Playwright needed
#
# Listing HTML structure (confirmed):
#   Plain <a href="https://news.microsoft.com/source/YYYY/MM/DD/slug/">Title</a>
#   <date string>                   ← text node after the anchor
#   [Company News]                  ← category label (always "Company News")
#
# Article body HTML structure (confirmed via og meta + WordPress):
#   <meta property="article:published_time" content="2026-05-21T11:00:07+00:00">
#   <div class="entry-content"> ← primary body container
# ─────────────────────────────────────────────

from datetime import datetime
from scrapers.base_scraper import BaseScraper

# ── Noise filter: skip purely administrative releases ──
# Microsoft's press-releases tag includes earnings announcements and
# routine admin notices alongside deal press releases.
SKIP_TITLE_FRAGMENTS = [
    "earnings press release available",   # "Microsoft earnings press release available on IR website"
    "to report",                          # "Microsoft to Report Q3 Results"
]


def _parse_date(raw: str) -> str:
    """
    Normalise Microsoft's date strings to ISO format YYYY-MM-DD.

    Input examples:
      "June 2, 2026"
      "May 21, 2026"
      "April 29, 2026"

    Returns "2026-06-02", "2026-05-21", etc.
    Falls back to raw string if parsing fails.
    """
    if not raw:
        return ""
    # Strip time portion if present — keep first 3 tokens "Month DD, YYYY"
    date_part = " ".join(raw.strip().split()[:3]).rstrip(",")
    try:
        return datetime.strptime(date_part, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Fallback: ISO datetime from og meta (article:published_time)
            return raw[:10]  # "2026-05-21T11:00:07+00:00" → "2026-05-21"
        except Exception:
            return raw


class MicrosoftScraper(BaseScraper):

    SOURCE_NAME = "Microsoft"
    BASE_URL    = "https://news.microsoft.com"
    NEWS_URL    = "https://news.microsoft.com/source/tag/press-releases/"

    # ── Parse press releases from listing page ──
    def parse_press_releases(self, soup):
        """
        Microsoft press-releases tag page HTML structure (WordPress):

          # Press releases  Results Page (10463 results)

          [https://news.microsoft.com/source/2026/06/02/slug/]   ← bare URL as text (skip)
          June 2, 2026                                           ← date text node
          [Mayo Clinic and Microsoft collaborate...]             ← <a href="URL">Title</a>
          [Company News]                                         ← category <a>

          [EY logo img]                                          ← optional image card
          May 21, 2026
          [EY and Microsoft announce global initiative...]
          [Company News]

        Each release appears as an <a> whose href starts with
        https://news.microsoft.com/source/YYYY/ — that's the selector.
        The preceding text node holds the date.
        """
        results = []
        seen    = set()

        anchors = soup.find_all(
            "a", href=lambda h: h and "news.microsoft.com/source/20" in h
        )

        for anchor in anchors:
            href  = anchor.get("href", "")
            title = anchor.get_text(strip=True)

            # Skip bare-URL text links (the plain URL printed as link text)
            if not title or title.startswith("http") or title == "Company News":
                continue

            if href in seen:
                continue
            seen.add(href)

            # Skip noise releases by title
            title_lower = title.lower()
            if any(frag in title_lower for frag in SKIP_TITLE_FRAGMENTS):
                continue

            # Date: walk backwards through siblings to find the date text node
            # Structure is: date_text → [optional img anchor] → title anchor
            date = ""
            for sibling in anchor.previous_siblings:
                text = sibling.get_text(strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
                if not text:
                    continue
                # Date strings look like "June 2, 2026" or "May 21, 2026"
                if any(month in text for month in [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ]):
                    date = _parse_date(text)
                    break

            results.append({
                "title": title,
                "url":   href,
                "date":  date,
            })

        print(f"  Found {len(results)} press release(s) on page")
        return results

    # ── Fetch full article body ──
    def fetch_article_body(self, url):
        """
        Microsoft article page structure (WordPress):

          <meta property="article:published_time" content="2026-05-21T11:00:07+00:00">

          <div class="entry-content">   ← primary body container
            <p>LONDON — May 21, 2026 — The EY organization and Microsoft Corp...</p>
            <p>...</p>
            <ul><li>...</li></ul>
            <h2>...</h2>
          </div>

        Fallback chain:
          div.entry-content → div.post-content → article → main
        """
        soup = self.fetch_page(url)

        # Try to get ISO date from og meta first (more reliable than listing scrape)
        published_meta = soup.find("meta", property="article:published_time")
        iso_date = ""
        if published_meta:
            content = published_meta.get("content", "")
            iso_date = content[:10]  # "2026-05-21T11:00:07+00:00" → "2026-05-21"

        # Primary body selector — WordPress standard
        body = soup.find("div", class_="entry-content")
        if not body:
            body = soup.select_one("div.post-content, div[class*='article-body']")
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
            if not text:
                continue
            # Stop at boilerplate — Microsoft ends with "Note to editors:"
            if text.startswith("Note to editors"):
                break
            paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text, iso_date

    # ── Override get_new_releases to capture iso_date from article page ──
    def get_new_releases(self, seen_urls):
        """
        Overrides base to use the more reliable ISO date from article og meta
        when available, falling back to the listing-page date string.
        """
        import time
        from config import REQUEST_DELAY

        soup     = self.fetch_main_page()
        releases = self.parse_press_releases(soup)
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
                "date":   iso_date or release["date"],  # prefer og meta date
                "body":   body,
            })

        print(f"[{self.SOURCE_NAME}] {len(new)} new release(s) found")
        return new
