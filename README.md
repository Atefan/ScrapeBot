# ScrapeBot

Monitors press releases from major tech company IR pages and GlobeNewswire RSS feeds for a watchlist of ~80 tickers. Each article is sent to Claude Haiku, which classifies it as an investment or partnership signal and outputs a BUY / WATCH / IGNORE recommendation. Actionable results are pushed to Telegram.

## Architecture

```
Scraper → AI Analyzer → Log → Mark seen → Telegram notify
```

Two scraper patterns:
- **HTML scrapers** (`scrapers/nvda_scraper.py`, `msft_scraper.py`, etc.) — extend `BaseScraper`, scrape company IR pages directly
- **GlobeNewswire** (`scrapers/globenewswire_scraper.py`) — reads 3 RSS feeds, filters entries by matching tickers against `WATCHLIST`, fetches body only for matches

See `CLAUDE.md` for full architecture details.

## Setup (Windows)

### 1. Environment variables
Set these as Windows **User** environment variables (System Properties → Advanced → Environment Variables):

```
ANTHROPIC_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Windows Scheduled Task
Create via Task Scheduler (full "Create Task" dialog, not the basic wizard):

- **Trigger:** Weekly, Mon–Fri, start 14:00, repeat every **30 minutes** for **8 hours** (stops at 22:00)
- **Action:**
  - Program: `cmd.exe`
  - Arguments: `/c python -X utf8 "C:\Users\stefa\source\ScrapeBot\main.py" >> "C:\Users\stefa\source\ScrapeBot\cron.log" 2>&1`
  - Start in: `C:\Users\stefa\source\ScrapeBot`
- **Settings:** "If already running, do not start a new instance"

## Running manually

```bash
python -X utf8 main.py       # full pipeline
python -X utf8 Tester.py     # GlobeNewswire scraper only, ignores seen_urls
```

`-X utf8` is required on Windows — without it, emoji print statements raise `UnicodeEncodeError` when output is redirected to a file.

## Key files

| Path | Purpose |
|---|---|
| `main.py` | Orchestrates the full pipeline |
| `config.py` | All settings: API keys, file paths, HTTP headers |
| `scrapers/` | One file per company + `base_scraper.py` + GlobeNewswire |
| `ai/analyzer.py` | Sends article to Claude Haiku, returns structured dict |
| `ai/prompts.py` | System prompt and user prompt builder — tune AI behavior here |
| `storage/seen_urls.py` | Deduplication: tracks every URL ever processed |
| `storage/log.py` | Append-only logs for releases and Telegram notifications |
| `notifications/telegram.py` | Sends Telegram messages |
| `data/` | Runtime state (gitignored) — seen URLs, release log, notification log |
| `cron.log` | Runtime output log (gitignored) — trimmed automatically at 1 MB |

## Tuning

- **AI classification logic** — edit `ai/prompts.py` (system prompt + JSON schema). Do not touch `ai/analyzer.py` for prompt changes.
- **Ticker watchlist** — edit `WATCHLIST` at the top of `scrapers/globenewswire_scraper.py`
- **Add a new company scraper** — create `scrapers/yourco_scraper.py` extending `BaseScraper`, implement `parse_press_releases()` and `fetch_article_body()`, then register the instance in `main.py`

## Known limitations

- `storage/log.py` rewrites the entire `releases_log.json` on every append — will get slow if the file grows large. Worth switching to newline-delimited JSON if needed.
- Commented-out test code at the bottom of `config.py` is dead — safe to delete.
