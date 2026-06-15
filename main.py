# ─────────────────────────────────────────────
# main.py — orchestrates the full pipeline
# ─────────────────────────────────────────────

import os
import traceback
from datetime import datetime

# ── Fix working directory for cron ──
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from scrapers.nvda_scraper import NvidiaScraper
from scrapers.meta_scraper import MetaScraper
from scrapers.amd_scraper import AMDScraper
from scrapers.msft_scraper import MicrosoftScraper
from scrapers.google_scraper import GoogleScraper
from scrapers.aapl_scraper import AppleScraper
from scrapers.avgo_scraper import BroadcomScraper
from scrapers.globenewswire_scraper import GlobeNewswireScraper

from storage.seen_urls import load_seen_urls, mark_as_seen
from storage.log import append_release, append_notification
from ai.analyzer import analyze
from notifications.telegram import send_notification

# ── Circular log — trim if over 1MB ──
LOG_FILE      = "cron.log"
LOG_MAX_BYTES = 1 * 1024 * 1024

def trim_log():
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > LOG_MAX_BYTES:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        keep = lines[len(lines) // 2:]
        with open(LOG_FILE, "w") as f:
            f.writelines(keep)
        print("  [log trimmed]")

# ── Register all scrapers here ──
SCRAPERS = [
    NvidiaScraper(),
    MetaScraper(),
    AMDScraper(),
    MicrosoftScraper(),
    GoogleScraper(),
    AppleScraper(),
    BroadcomScraper(),
    GlobeNewswireScraper(),
]


def build_telegram_message(release: dict, ai: dict) -> str:
    rec   = ai.get("recommendation", "?")
    emoji = {"BUY": "🟢", "WATCH": "🟡", "IGNORE": "⚪"}.get(rec, "⚪")
    return (
        f"{emoji} <b>{rec} — {ai.get('partner_ticker') or 'Unknown'}</b>\n\n"
        f"<b>Source:</b> {release.get('source')}\n"
        f"<b>Published:</b> {release.get('date') or 'Unknown'}\n"
        f"<b>Partner:</b> {ai.get('partner_name') or 'N/A'}\n"
        f"<b>Deal:</b> {ai.get('deal_type') or 'N/A'}\n"
        f"<b>Size:</b> {ai.get('deal_size') or 'Not disclosed'}\n\n"
        f"<b>Significance:</b>\n{ai.get('significance') or 'N/A'}\n\n"
        f"<b>Reasoning:</b>\n{ai.get('reasoning') or 'N/A'}\n\n"
        f"<b>Confidence:</b> {ai.get('confidence') or 'N/A'}\n"
        f"<a href=\"{release.get('url')}\">Read Press Release</a>"
    )


def notify_error(step: str, release: dict | None, error: Exception):
    title = release.get("title", "Unknown")[:60] if release else "N/A"
    tb    = traceback.format_exc()[-800:]

    message = (
        f"🔴 <b>Bot Error — {step}</b>\n\n"
        f"<b>Article:</b> {title}\n\n"
        f"<b>Error:</b> <code>{type(error).__name__}: {str(error)[:200]}</code>\n\n"
        f"<b>Traceback:</b>\n<code>{tb}</code>"
    )
    try:
        send_notification(message, silent=True)
    except Exception as e:
        print(f"  WARNING: Could not send error notification: {e}")


def run():
    trim_log()

    print(f"\n{'='*55}")
    print(f"  Bot run started: {datetime.utcnow().isoformat()}")
    print(f"{'='*55}")

    try:
        seen_urls = load_seen_urls()
    except Exception as e:
        notify_error("load_seen_urls", None, e)
        print(f"CRITICAL: Could not load seen_urls — aborting. {e}")
        return

    total_new = 0

    for scraper in SCRAPERS:

        try:
            new_releases = scraper.get_new_releases(seen_urls)
        except Exception as e:
            notify_error(f"Scraper [{scraper.SOURCE_NAME}]", None, e)
            print(f"  ERROR in scraper {scraper.SOURCE_NAME}: {e} — skipping")
            continue

        for release in new_releases:

            # ── Step 2: AI analysis ──
            try:
                ai_result = analyze(release)
                release["ai"] = ai_result
            except Exception as e:
                notify_error("AI Analyzer", release, e)
                print(f"  ERROR in analyzer for '{release['title'][:50]}': {e}")
                release["ai"] = {
                    "classification": "ERROR",
                    "recommendation": "IGNORE",
                    "error":          str(e)
                }

            # ── Step 3: log ──
            try:
                append_release(release)
            except Exception as e:
                notify_error("append_release", release, e)
                print(f"  ERROR writing to log: {e}")

            # ── Step 4: mark as seen ──
            try:
                mark_as_seen(release["url"], seen_urls)
            except Exception as e:
                notify_error("mark_as_seen", release, e)
                print(f"  ERROR marking URL as seen: {e}")

            # ── Step 5: notify if actionable ──
            ai  = release.get("ai", {})
            rec = ai.get("recommendation", "IGNORE")

            if rec == "IGNORE":
                print(f"  Skipping notification — IGNORE")
            else:
                try:
                    message = build_telegram_message(release, ai)
                    result  = send_notification(message)
                    append_notification({
                        "url":             release["url"],
                        "title":           release["title"],
                        "recommendation":  rec,
                        "partner_ticker":  ai.get("partner_ticker"),
                        "telegram_result": result,
                    })
                    print(f"  Telegram sent → {rec} {ai.get('partner_ticker') or ''}")
                except Exception as e:
                    notify_error("Telegram notification", release, e)
                    print(f"  ERROR sending Telegram: {e}")

            total_new += 1

    print(f"\n{'='*55}")
    print(f"  Done. {total_new} new release(s) processed.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()