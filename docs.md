[Scheduler] → [Scraper] → [AI Analyzer] → [Decision Logger] → [Phone Notification]
1. The Scraper
    - Language: Python (best ecosystem for this)

    - Playwright (for JS-rendered pages)
    - SQLite (Store a hash or timestamp of already-seen articles so you don't re-process old ones)
    - Run on a cron job (every 15–30 min)

Pages to watch(in the fture large cap companies):

NVIDIA -    nvidianews.nvidia.com/news
Microsoft - news.microsoft.com/category/business
Meta -      investor.fb.com/news
Google -    blog.google/inside-google
AMD -       ir.amd.com/news-events/press-releases
AAPL -
AMZN - 
TSLA - 
PLTR - 

2. The AI Analyzer

"Does this press release describe NVIDIA investing money into, or forming a deep strategic partnership with, a publicly traded company?"

Two-stage thinking:

Stage 1 — Is this relevant?
    Many press releases are product launches, executive hires, award wins, quarterly results. We don't care about those. The AI should first decide:

    INVESTMENT — NVIDIA put cash into a company (like CoreWeave $2B)
    PARTNERSHIP — deep strategic integration, joint development (like TSMC)
    PRODUCT — just a product announcement, no partner play
    IGNORE — earnings, awards, hiring, unrelated news

    Only INVESTMENT and PARTNERSHIP go further. Everything else is logged but no notification sent.
Stage 2 — Extract the details
    If relevant, pull:

    Partner company name
    Partner ticker symbol
    Type of deal (cash investment / licensing / joint development / reseller)
    Deal size if mentioned
    Strategic significance in plain English
    Recommendation: BUY / WATCH / IGNORE
    Confidence: High / Medium / Low
    Reasoning in 2 sentences

Responce:
{
    "classification":  "INVESTMENT",       # or PARTNERSHIP / PRODUCT / IGNORE
    "partner_name":    "Marvell Technology",
    "partner_ticker":  "MRVL",
    "deal_type":       "Strategic equity investment",
    "deal_size":       "$2,000,000,000",   # None if not mentioned
    "significance":    "NVIDIA takes $2B stake in Marvell and integrates
                        their chips into NVLink Fusion — deep hardware lock-in.",
    "recommendation":  "BUY",             # BUY / WATCH / IGNORE
    "confidence":      "High",
    "reasoning":       "Cash investment + hardware integration = direct
                        revenue impact on MRVL. High conviction play.",
    "analyzed_at":     "2026-06-04T10:00:05Z"
}

3. Log File
Simple structured JSON or CSV log:
json{
  "date": "2026-06-04",
  "source": "NVIDIA Newsroom",
  "headline": "NVIDIA and Marvell...",
  "partner_ticker": "MRVL",
  "recommendation": "BUY",
  "reasoning": "Strategic $2B investment signals...",
  "article_url": "..."
}

4. Phone Notification
Easiest options:

Pushover (simplest — $5 one-time app purchase, dead simple API)
Telegram Bot (free, just create a bot via @BotFather)
Pushbullet (free tier available)

Telegram is probably the best — free, reliable, and you can also send the full AI summary directly to your phone as a message.

5. Hosting (for later)
OptionCostBest forRailway.app~$5/moEasy Python deploymentRender.comFree tierGood starting pointVPS (Hetzner/DigitalOcean)~$5/moFull controlAWS Lambda + EventBridgeNear freeServerless cron
A simple VPS or Railway is easiest for a Python cron script.

💰 Token Usage & API Costs
What are tokens?

Roughly 1 token ≈ 4 characters of text
A typical press release is ~500–1,500 words ≈ 700–2,000 tokens input
Your AI response/analysis ≈ 200–300 tokens output


~1,500 input tokens = $0.0045
~300 output tokens = $0.0045
≈ $0.01 per article — essentially negligible

If you scan 10 companies, check every 30 min, 5 new articles/day:

~50 articles/day × $0.01 = ~$0.50/day or ~$15/month

TOFIGURE:



TODO:
1. Scrape NVDA
    1.1. Scrape the main page   
    1.2. Check if new Press Release   
    1.3. Scrape new Press Release
    1.4. Process info before submit
    1.5. Send to AI with prompt

    Notes:
    - Probably a custom scraper for every site? (start with just NVDA)
    - 54 articles last year from NVDA

2. Send the prompt / Receive the result

3. Log and Send Notification
    

    