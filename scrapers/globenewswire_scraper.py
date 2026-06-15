# ─────────────────────────────────────────────
# scrapers/globenewswire_scraper.py
# ─────────────────────────────────────────────

import time
import feedparser
from config import HEADERS, REQUEST_DELAY
from scrapers.base_scraper import BaseScraper

WATCHLIST = [
    # ── Mega Cap Tech ──
    "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:NVDA", "NASDAQ:AMZN",
    "NASDAQ:META", "NASDAQ:GOOGL", "NASDAQ:GOOG", "NASDAQ:TSLA",
    "NASDAQ:AVGO", "NASDAQ:ASML",

    # ── Semiconductors ──
    "NASDAQ:AMD", "NASDAQ:QCOM", "NASDAQ:TXN", "NASDAQ:INTC",
    "NASDAQ:AMAT", "NASDAQ:MU", "NASDAQ:LRCX", "NASDAQ:KLAC",
    "NASDAQ:MRVL", "NASDAQ:ARM",

    # ── Software ──
    "NASDAQ:ADBE", "NASDAQ:INTU", "NASDAQ:CRWD", "NASDAQ:PANW",
    "NASDAQ:SNPS", "NASDAQ:CDNS", "NASDAQ:FTNT", "NASDAQ:TEAM",
    "NASDAQ:WDAY", "NASDAQ:ZS", "NASDAQ:DDOG", "NASDAQ:NET",
    "NYSE:CRM", "NYSE:NOW", "NYSE:SNOW",

    # ── Cloud / Internet ──
    "NASDAQ:NFLX", "NASDAQ:CSCO", "NASDAQ:PYPL", "NASDAQ:ABNB",
    "NASDAQ:SHOP", "NYSE:UBER", "NYSE:LYFT",

    # ── Finance & Payments ──
    "NYSE:JPM", "NYSE:BAC", "NYSE:GS", "NYSE:MS", "NYSE:V",
    "NYSE:MA", "NYSE:AXP", "NYSE:BLK", "NYSE:C", "NYSE:WFC",
    "NASDAQ:COIN", "NASDAQ:MSTR",

    # ── E-Commerce / Retail ──
    "NASDAQ:COST", "NYSE:WMT", "NYSE:TGT", "NYSE:HD", "NASDAQ:MELI",

    # ── Healthcare & Biotech ──
    "NASDAQ:AMGN", "NASDAQ:GILD", "NASDAQ:REGN", "NASDAQ:VRTX",
    "NASDAQ:BIIB", "NASDAQ:MRNA", "NASDAQ:IDXX",
    "NYSE:JNJ", "NYSE:PFE", "NYSE:UNH", "NYSE:LLY", "NYSE:ABT", "NYSE:TMO",

    # ── Energy ──
    "NYSE:XOM", "NYSE:CVX", "NYSE:COP", "NYSE:SLB", "NYSE:NEE",

    # ── Consumer & Media ──
    "NYSE:DIS", "NASDAQ:CMCSA", "NYSE:NKE", "NYSE:KO",
    "NYSE:PEP", "NYSE:MCD", "NYSE:SBUX",

    # ── Industrials & Defense ──
    "NYSE:BA", "NYSE:LMT", "NYSE:RTX", "NYSE:CAT", "NYSE:GE", "NYSE:HON",

    # ── EV & Future Tech ──
    "NYSE:RIVN", "NYSE:F", "NYSE:GM", "NASDAQ:LCID",
]

RSS_FEEDS = {
    "mergers":    "https://www.globenewswire.com/RssFeed/subjectcode/27-Mergers%20and%20Acquisitions",
    "public_cos": "https://www.globenewswire.com/RssFeed/orgclass/1",
    "analyst":    "https://www.globenewswire.com/RssFeed/subjectcode/3-Analyst%20Recommendations",
}


class GlobeNewswireScraper(BaseScraper):

    SOURCE_NAME = "GlobeNewswire"
    NEWS_URL    = "https://www.globenewswire.com"

    def fetch_main_page(self):
        pass

    def parse_press_releases(self, soup):
        pass

    def fetch_article_body(self, url):
        soup = self.fetch_page(url)

        body = soup.find("div", class_="article-body") \
            or soup.find("article")

        if not body:
            print("  WARNING: article body not found")
            return ""

        for tag in body.find_all(["script", "style", "img", "figure", "nav"]):
            tag.decompose()

        paragraphs = []
        for element in body.find_all(["p", "li", "h2", "h3"]):
            text = element.get_text(strip=True)
            if text:
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)
        print(f"  Extracted {len(full_text):,} chars")
        return full_text

    def get_new_releases(self, seen_urls: set) -> list:
        print(f"\n[{self.SOURCE_NAME}] Polling {len(RSS_FEEDS)} RSS feeds...")
        candidates  = []
        seen_in_run = set()

        for feed_name, feed_url in RSS_FEEDS.items():
            print(f"  RSS [{feed_name}]: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
            except Exception as e:
                print(f"  ERROR parsing feed {feed_name}: {e}")
                continue

            for entry in feed.entries:
                title   = entry.get("title",    "No title")
                url     = entry.get("link",     "")
                date    = entry.get("published", "")
                summary = entry.get("summary",  "")

                if url in seen_urls or url in seen_in_run:
                    continue

                # Extract only stock tickers
                entry_tickers = [
                    tag["term"].upper()
                    for tag in entry.get("tags", [])
                    if tag.get("scheme") == "https://www.globenewswire.com/rss/stock"
                ]

                matched = [w for w in WATCHLIST if w.upper() in entry_tickers]
                if not matched:
                    continue

                breakpoint()
                print(f"  HIT [{', '.join(matched)}]: {title[:65]}")
                candidates.append({
                    "url":     url,
                    "title":   title,
                    "date":    date,
                    "summary": summary,
                })
                seen_in_run.add(url)

        new = []
        for release in candidates:
            time.sleep(REQUEST_DELAY)
            body = self.fetch_article_body(release["url"])
            new.append({
                "source": self.SOURCE_NAME,
                "title":  release["title"],
                "url":    release["url"],
                "date":   release["date"],
                "body":   body or release["summary"],
            })

        print(f"[{self.SOURCE_NAME}] {len(new)} new release(s) found")
        return new