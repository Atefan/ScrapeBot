[Scheduler] → [Scraper] → [AI Analyzer] → [Decision Logger] → [Phone Notification]
1. The Scraper
    - Language: Python (best ecosystem for this)

    - BeautifulSoup (for HTML-rendered pages)
    - feedparser (for RSS_FEEDS-rendered pages)
    - Run on a cron job (every 5 min)

Pages to watch(in the fture large cap companies):

NVDA  - https://nvidianews.nvidia.com/news?page=1
AAPL - 	https://www.apple.com/newsroom/rss-feed.rss
AMD -	https://ir.amd.com/news-events/press-releases
AVGO -	https://investors.broadcom.com/financial-information/financial-news-releases
GOOGLE	https://blog.google/rss/    //  https://abc.xyz/investor/news/
META - 	https://news.microsoft.com/source/tag/press-releases/
MSFT - 	https://news.microsoft.com/source/tag/press-releases/
RSS [earnings]:		https://www.globenewswire.com/RssFeed/subjectcode/13-Earnings%20Releases%20and%20Operating%20Results
RSS [public_cos]:	https://www.globenewswire.com/RssFeed/orgclass/1
RSS [analyst]:		https://www.globenewswire.com/RssFeed/subjectcode/3-Analyst%20Recommendations


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

PROMPT:
    You are a financial analyst specializing in technology sector investments.
    You analyze press releases from major tech companies (NVIDIA, Microsoft, AMD, etc.)
    to identify investment opportunities in their partners and portfolio companies.

    Your job is to read a press release and determine:
    1. Whether it describes an investment or significant partnership with another company
    2. Extract key details about that company and the deal
    3. Make a trading recommendation

    You must respond ONLY with a valid JSON object. No preamble, no explanation, no markdown
    code blocks. Just the raw JSON.

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
  {
    "source": "NVIDIA",
    "title": "NVIDIA and TSMC Bring AI Into Fabs to Advance Semiconductor Design and Manufacturing",
    "url": "/news/nvidia-and-tsmc-bring-ai-into-fabs-to-advance-semiconductor-design-and-manufacturing",
    "date": "May 31, 2026",
    "body": "News Summary:\n\nNVIDIA CUDA-X libraries and AI models are accelerating TSMC ...",
    "ai": {
      "classification": "PARTNERSHIP",
      "partner_name": "Taiwan Semiconductor Manufacturing Company",
      "partner_ticker": "TSM",
      "deal_type": "Strategic technology partnership and joint product development",
      "deal_size": null,
      "significance": "TSMC is integrating NVIDIA's accelerated computing and AI technologies across its entire semiconductor ...
      "recommendation": "WATCH",
      "confidence": "High",
      "reasoning": "This is a confirmed deep partnership with clear strategic significance and multiple...
      "analyzed_at": "2026-06-05T13:07:34.769631"
    },
    "logged_at": "2026-06-05T13:07:42.207534"
  },

4. Phone Notification

Telegram Bot   