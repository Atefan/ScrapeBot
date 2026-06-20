# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the bot

```bash
python -X utf8 main.py          # full pipeline run (scrape → AI → log → Telegram)
python -X utf8 Tester.py        # manual scraper test (GlobeNewswire only, empty seen_urls)
```

The `-X utf8` flag is required on Windows to prevent UnicodeEncodeError when emoji characters are printed and stdout is redirected to `cron.log`.

The bot runs via a Windows Scheduled Task (every 30 min, Mon–Fri, 14:00–22:00). `main.py` sets `os.chdir` to its own directory so the task invocation works correctly regardless of working directory.

## Required environment variables

```
ANTHROPIC_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

## Dependencies

```bash
pip install -r requirements.txt
```

Packages: `requests`, `beautifulsoup4`, `feedparser`. The `anthropic` SDK is not used — the AI call goes via raw HTTP in `ai/analyzer.py`.

## Architecture

The pipeline is a linear chain: **Scrape → AI analyze → Log → Mark seen → Telegram notify**

`main.py` orchestrates everything. It loops over a list of scraper instances, calls `get_new_releases(seen_urls)` on each, then for every new release runs the AI, logs the result, marks the URL as seen, and sends a Telegram notification if the recommendation is not IGNORE.

### Two scraper patterns

All HTML scrapers extend `BaseScraper` and implement two methods:
- `parse_press_releases(soup)` — extracts `{title, url, date}` dicts from the listing page
- `fetch_article_body(url)` — fetches the article page and returns clean text

`GlobeNewswireScraper` is the exception: it overrides `get_new_releases` entirely because it reads RSS feeds instead of scraping HTML. It filters entries by matching their stock tickers against `WATCHLIST` (defined at the top of that file) and only fetches body text for matching articles.

### AI layer

`ai/analyzer.py` calls Claude Haiku via raw HTTP (not the SDK). The prompt and JSON schema live in `ai/prompts.py` — edit there to tune AI behavior without touching logic. The analyzer retries once on JSON parse failure and always returns a dict (error dict on total failure).

### Storage

- `data/seen_urls.json` — set of all processed URLs; loaded once per run, updated after each article
- `data/releases_log.json` — append-only list of every release with its full AI result
- `data/notifications_log.json` — log of every Telegram message sent

All three files are created automatically on first write.

## Known issues / gotchas

- The `config.py` bottom section is dead commented-out test code — safe to delete.
- `storage/log.py` rewrites the entire JSON file on every append — will get slow with a large `releases_log.json`.
- The AI call uses `requests` directly; if you switch to the `anthropic` SDK, update `ai/analyzer.py`.
