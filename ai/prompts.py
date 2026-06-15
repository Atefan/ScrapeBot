# ─────────────────────────────────────────────
# ai/prompts.py
# All prompt templates in one place.
# Edit these to tune the AI behavior without
# touching any logic files.
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a financial analyst specializing in technology sector investments.
You analyze press releases from major tech companies (NVIDIA, Microsoft, AMD, etc.)
to identify investment opportunities in their partners and portfolio companies.

Your job is to read a press release and determine:
1. Whether it describes an investment or significant partnership with another company
2. Extract key details about that company and the deal
3. Make a trading recommendation

You must respond ONLY with a valid JSON object. No preamble, no explanation, no markdown
code blocks. Just the raw JSON.
""".strip()


def build_analysis_prompt(title: str, body: str) -> str:
    """
    Builds the user message sent to Claude Haiku.
    Returns the full prompt string.
    """
    return f"""
Analyze this press release and return a JSON object with the exact schema below.

PRESS RELEASE TITLE:
{title}

PRESS RELEASE BODY:
{body}

CLASSIFICATION RULES:
- "INVESTMENT"   → the announcing company put actual cash / equity into another company
- "PARTNERSHIP"  → deep strategic integration, joint product development, or major supplier deal
- "PRODUCT"      → product launch or update with no named external company as a key partner
- "IGNORE"       → earnings report, award, hiring announcement, or other non-actionable news

RECOMMENDATION RULES:
- "BUY"   → cash investment confirmed, or partnership with clear direct revenue impact
- "WATCH" → strong partnership but no cash investment confirmed yet
- "IGNORE"→ classification is PRODUCT or IGNORE, or partner is not publicly traded

CONFIDENCE RULES:
- "High"   → deal size mentioned, ticker is well known, strategic fit is clear
- "Medium" → partnership confirmed but details are vague or partner is smaller
- "Low"    → speculative reading, no explicit commitment language

REQUIRED JSON SCHEMA — return exactly this structure, null for unknown fields:
{{
    "classification":  "INVESTMENT | PARTNERSHIP | PRODUCT | IGNORE",
    "partner_name":    "Full company name or null",
    "partner_ticker":  "TICKER or null",
    "deal_type":       "e.g. Strategic equity investment / Joint development / Reseller agreement or null",
    "deal_size":       "e.g. $2,000,000,000 or null if not mentioned",
    "significance":    "1-2 sentence plain English summary of why this matters or null",
    "recommendation":  "BUY | WATCH | IGNORE",
    "confidence":      "High | Medium | Low",
    "reasoning":       "2 sentence max — why this recommendation, what is the expected impact",
    "date":       "DD.MM.YYYY post upload date"
}}

Return ONLY the JSON object. No other text.
""".strip()
