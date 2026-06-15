# ─────────────────────────────────────────────
# scrapers/meta_scraper.py
# Meta-specific scraper
# HTML structure confirmed by inspection June 2026
# Listing: https://about.fb.com/news/tag/infrastructure/
# Articles: WordPress CMS, server-rendered
# ─────────────────────────────────────────────

from scrapers.base_scraper import BaseScraper


class MetaScraper(BaseScraper):

    SOURCE_NAME = "Meta"
    BASE_URL    = "https://about.fb.com"
    NEWS_URL    = "https://about.fb.com/news/tag/infrastructure/"

    # ── Parse press releases from infrastructure tag page ──
    def parse_press_releases(self, soup):
        """
        Meta infrastructure tag page — only contains deal/investment articles.
        No category filtering needed; the tag itself is the filter.

        HTML structure:
          <article class="post-...">
            <h3>
              <a href="https://about.fb.com/news/2026/01/...">Title</a>
            </h3>
            <time datetime="2026-01-27">January 27, 2026</time>
          </article>
        """
        articles = soup.find_all("article")
        results  = []
        seen     = set()

        for article in articles:
            # Title + URL
            heading = article.find(["h2", "h3"])
            anchor  = heading.find("a") if heading else None
            if not anchor:
                anchor = article.find("a", href=lambda h: h and "/news/20" in h)
            if not anchor:
                continue

            url   = anchor.get("href", "")
            title = anchor.get_text(strip=True)

            if not url or not title:
                continue
            if url.startswith("/"):
                url = self.BASE_URL + url
            if url in seen:
                continue
            seen.add(url)

            # Date
            date    = ""
            date_el = article.select_one("time, [class*='date'], [class*='Date']")
            if date_el:
                date = date_el.get("datetime", "") or date_el.get_text(strip=True)

            results.append({
                "title": title,
                "url":   url,
                "date":  date,
            })

        print(f"  Found {len(results)} infrastructure release(s) on page")
        return results

    # ── Fetch full article body ──
    def fetch_article_body(self, url):
        """
        Meta article page structure (WordPress):

          <div class="entry-content">   ← primary body container
            <p>...</p>
            <ul><li>...</li></ul>
            <h2>...</h2>
          </div>

        Fallback chain:
          div.post-content → div[class*='article-body'] → article → main
        """
        soup = self.fetch_page(url)

        body = soup.find("div", class_="entry-content")
        if not body:
            body = soup.select_one("div.post-content, div[class*='article-body']")
        if not body:
            body = soup.find("article")
        if not body:
            body = soup.find("main")

        if not body:
            print("  WARNING: no article body found")
            return ""

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
        return full_text
