# ─────────────────────────────────────────────
# scrapers/amd_scraper.py
# AMD-specific scraper
# HTML structure confirmed by inspection June 2026
#
# Listing page:  https://ir.amd.com/news-events/press-releases
# Example article (exemplary deal press release):
#   https://ir.amd.com/news-events/press-releases/detail/1286/
#   amd-announces-more-than-10-billion-in-taiwan-ecosystem-investments
#
# Platform: Q4 IR (same as most NASDAQ IR sites)
# Server-rendered HTML — no Playwright needed
# ─────────────────────────────────────────────

from scrapers.base_scraper import BaseScraper

# ── Noise filter: skip purely administrative releases ──
# AMD posts earnings calls, meeting notices, and financial result
# announcements alongside deal press releases. These are identifiable
# by their title patterns and are irrelevant for investment signals.
SKIP_TITLE_FRAGMENTS = [
    "to report",           # "AMD to Report First Quarter..."
    "to host",             # "AMD to Host Annual Meeting..."
    "annual meeting",      # "AMD to Host Annual Meeting of Stockholders"
]


class AMDScraper(BaseScraper):

    SOURCE_NAME = "AMD"
    BASE_URL    = "https://ir.amd.com"
    NEWS_URL    = "https://ir.amd.com/news-events/press-releases"

    # ── Parse press releases from listing page ──
    def parse_press_releases(self, soup):
        """
        AMD IR listing HTML structure (Q4 IR platform):

          # Press Releases                          ← h1 page heading

          [AMD Announces $10B Taiwan Investments]   ← plain <a href="/news-events/press-releases/detail/1286/...">
          May 21, 2026 1:35 am EDT                 ← plain text node after the <a>

          [AMD and Meta Announce Partnership...]
          Feb 24, 2026 7:00 am EST

        Critically: NO wrapping <article> or <li> tags.
        Each release is just a bare <a> followed by a date string.
        We collect all <a> tags pointing to /news-events/press-releases/detail/.
        """
        results = []
        seen    = set()

        # Every release link points to this path pattern
        anchors = soup.find_all(
            "a", href=lambda h: h and "/news-events/press-releases/detail/" in h
        )

        for anchor in anchors:
            href  = anchor.get("href", "")
            title = anchor.get_text(strip=True)

            if not href or not title:
                continue

            # Build absolute URL
            if href.startswith("/"):
                href = self.BASE_URL + href
            if href in seen:
                continue
            seen.add(href)

            # Skip admin/noise releases by title
            title_lower = title.lower()
            if any(frag in title_lower for frag in SKIP_TITLE_FRAGMENTS):
                continue

            # Date: the text node immediately following the <a> tag
            # It looks like: "\nMay 21, 2026 1:35 am EDT\n"
            date = ""
            next_node = anchor.next_sibling
            if next_node and isinstance(next_node, str):
                date = next_node.strip().split("\n")[0].strip()

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
        AMD article page structure (Q4 IR platform):

          <h1>AMD Announces More Than $10 Billion...</h1>
          <p>May 21, 2026 1:35 am EDT</p>           ← date/meta line
          <a>Download as PDF</a>                     ← skip
          <p>News Summary:</p>
          <ul><li>$10B investment...</li></ul>
          <p>SANTA CLARA, Calif... (GLOBE NEWSWIRE)...</p>
          ...body paragraphs...
          <p>About AMD</p>                           ← boilerplate starts here
          <p>Cautionary Statement...</p>             ← legal boilerplate

        The entire article lives in the <main> / #mainContent element.
        We stop collecting at "About AMD" to avoid boilerplate.
        """
        soup = self.fetch_page(url)

        # Primary container on Q4 IR platform
        body = soup.find(id="mainContent")
        if not body:
            body = soup.find("main")
        if not body:
            body = soup.find("div", class_=lambda c: c and "article" in c.lower())

        if not body:
            print("  WARNING: no article body found")
            return ""

        # Strip noise tags
        for tag in body.find_all(["script", "style", "img", "figure",
                                   "nav", "aside", "header", "footer"]):
            tag.decompose()

        paragraphs = []
        for element in body.find_all(["p", "li", "h2", "h3", "h4"]):
            text = element.get_text(strip=True)
            if not text:
                continue
            # Stop at boilerplate sections — everything after is legal/about copy
            if text.startswith("About AMD") or text.startswith("Cautionary Statement"):
                break
            paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text
