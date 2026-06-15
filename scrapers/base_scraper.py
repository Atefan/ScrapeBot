# ─────────────────────────────────────────────
# scrapers/base_scraper.py
# Abstract base class — all scrapers inherit from this
# ─────────────────────────────────────────────

import requests
from bs4 import BeautifulSoup
from config import HEADERS, REQUEST_DELAY
import time


class BaseScraper:
    """
    Every company scraper inherits from this.
    Only override what's different per site.
    """

    SOURCE_NAME = "Base"        # e.g. "NVIDIA", "MSFT"
    NEWS_URL    = ""            # main news page URL

    # ── Fetch any page and return a BeautifulSoup object ──
    def fetch_page(self, url):
        print(f"  GET {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    # ── Fetch main news listing page ──
    def fetch_main_page(self):
        print(f"\n[{self.SOURCE_NAME}] Fetching main page: {self.NEWS_URL}")
        return self.fetch_page(self.NEWS_URL)

    # ── Parse press releases from the listing page ──
    # Each subclass implements this differently
    def parse_press_releases(self, soup):
        raise NotImplementedError("Each scraper must implement parse_press_releases()")

    # ── Fetch full article body text ──
    # Each subclass implements this differently
    def fetch_article_body(self, url):
        raise NotImplementedError("Each scraper must implement fetch_article_body()")

    # ── Full run: fetch page → parse → return new releases with body text ──
    def get_new_releases(self, seen_urls):
        """
        Main method called by main.py.
        Returns a list of new release dicts (not yet seen).
        Each dict has: title, url, date, body, source
        """
        soup     = self.fetch_main_page()
        releases = self.parse_press_releases(soup)
        new      = []

        for release in releases:
            if release["url"] in seen_urls:
                print(f"  SKIP: {release['title'][:65]}")
                continue

            print(f"  NEW:  {release['title'][:65]}")
            time.sleep(REQUEST_DELAY)

            body = self.fetch_article_body(release["url"])
            new.append({
                "source": self.SOURCE_NAME,
                "title":  release["title"],
                "url":    release["url"],
                "date":   release["date"],
                "body":   body,
            })

        print(f"[{self.SOURCE_NAME}] {len(new)} new release(s) found")
        return new
