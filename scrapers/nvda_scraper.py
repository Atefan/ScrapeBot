# ─────────────────────────────────────────────
# scrapers/nvda_scraper.py
# NVIDIA-specific scraper
# HTML structure confirmed by inspection June 2026
# ─────────────────────────────────────────────

import requests
from bs4 import BeautifulSoup
from config import HEADERS
from scrapers.base_scraper import BaseScraper


class NvidiaScraper(BaseScraper):

    SOURCE_NAME = "NVIDIA"
    BASE_URL    = "https://nvidianews.nvidia.com"
    NEWS_URL    = "https://nvidianews.nvidia.com/news"

    # ── 1.2  Parse press releases from main listing page ──
    def parse_press_releases(self, soup):
        """
        NVIDIA HTML structure:
          <article class="index-item">
            <h3 class="index-item-text-title"><a href="URL">Title</a></h3>
            <span class="index-item-text-info-date">June 03, 2026</span>
            <div class="index-item-text-link"><a>Read Press Release</a></div>
          </article>

        Filter: only keep articles where link text is "Read Press Release"
        """
        articles = soup.find_all("article", class_="index-item")
        results  = []

        for article in articles:
            # Filter by link button text
            link_div  = article.find("div", class_="index-item-text-link")
            link_text = link_div.get_text(strip=True) if link_div else ""
            if "press release" not in link_text.lower():
                continue

            # Title + URL
            title_tag = article.find("h3", class_="index-item-text-title")
            anchor    = title_tag.find("a") if title_tag else None
            title     = anchor.get_text(strip=True) if anchor else "No title"
            url       = anchor["href"]        if anchor else ""

            # Date
            date_tag  = article.find("span", class_="index-item-text-info-date")
            date_str  = date_tag.get_text(strip=True) if date_tag else ""

            results.append({
                "title": title,
                "url":   url,
                "date":  date_str,
            })

        print(f"  Found {len(results)} press release(s) on page")
        return results

    # ── 1.3  Fetch full article body ──
    def fetch_article_body(self, url):
        """
        NVIDIA article page structure:
          <div class="article-body"> ← all press release text lives here

        Strips scripts, styles, images. Joins paragraphs with double newline.
        """
        soup = self.fetch_page(self.BASE_URL + url)
        body = soup.find("div", class_="article-body")

        if not body:
            print("  WARNING: article-body div not found")
            return ""

        # Remove noise tags
        for tag in body.find_all(["script", "style", "img", "figure"]):
            tag.decompose()

        # Extract clean text paragraph by paragraph
        paragraphs = []
        for element in body.find_all(["p", "li", "h2", "h3"]):
            text = element.get_text(strip=True)
            if text:
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text
