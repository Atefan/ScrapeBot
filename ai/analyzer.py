# ─────────────────────────────────────────────
# ai/analyzer.py
# Sends press release text to Claude Haiku.
# Returns a structured dict with the AI result.
# ─────────────────────────────────────────────

import json
import requests
from datetime import datetime
from config import ANTHROPIC_API_KEY
from ai.prompts import SYSTEM_PROMPT, build_analysis_prompt

HAIKU_MODEL  = "claude-haiku-4-5-20251001"
API_URL      = "https://api.anthropic.com/v1/messages"
MAX_TOKENS   = 512       # analysis response is short — 512 is plenty
MAX_RETRIES  = 2         # retry once on JSON parse failure


# ─────────────────────────────────────────────
# Internal — raw API call
# ─────────────────────────────────────────────
def _call_haiku(title: str, body: str) -> str:
    """
    Sends the press release to Claude Haiku.
    Returns the raw text response string.
    Raises on HTTP errors.
    """
    headers = {
        "x-api-key":         ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    payload = {
        "model":      HAIKU_MODEL,
        "max_tokens": MAX_TOKENS,
        "system":     SYSTEM_PROMPT,
        "messages": [
            {
                "role":    "user",
                "content": build_analysis_prompt(title, body)
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data["content"][0]["text"].strip()


# ─────────────────────────────────────────────
# Internal — parse JSON from Haiku response
# ─────────────────────────────────────────────
def _parse_response(raw: str) -> dict:
    """
    Parses the raw text response into a dict.
    Strips markdown code fences if Haiku adds them despite instructions.
    Raises json.JSONDecodeError if parsing fails.
    """
    # Strip ```json ... ``` fences just in case
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    return json.loads(clean)


# ─────────────────────────────────────────────
# Public — main entry point
# ─────────────────────────────────────────────
def analyze(release: dict) -> dict:
    """
    Analyzes a press release dict (must have 'title' and 'body').
    Returns the ai result dict, always — even on failure.

    On success:
        { classification, partner_name, partner_ticker, deal_type,
          deal_size, significance, recommendation, confidence,
          reasoning, analyzed_at }

    On failure:
        { classification: "ERROR", error: "...", analyzed_at: "..." }
    """
    title = release.get("title", "")
    body  = release.get("body",  "")

    print(f"  Analyzing: {title[:65]}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw    = _call_haiku(title, body)
            result = _parse_response(raw)

            result["analyzed_at"] = datetime.now(datetime.UTC).isoformat()

            print(f"  → [{result.get('classification')}] "
                  f"Partner: {result.get('partner_ticker') or 'N/A'} | "
                  f"Rec: {result.get('recommendation')}")

            return result

        except json.JSONDecodeError as e:
            print(f"  WARNING: JSON parse failed (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                break

        except requests.HTTPError as e:
            print(f"  ERROR: API call failed: {e}")
            break

    # If all retries fail, return a safe error dict
    return {
        "classification": "ERROR",
        "partner_name":   None,
        "partner_ticker": None,
        "deal_type":      None,
        "deal_size":      None,
        "significance":   None,
        "recommendation": "IGNORE",
        "confidence":     None,
        "reasoning":      None,
        "error":          "Analysis failed after retries",
        "analyzed_at":    datetime.now(datetime.UTC).isoformat()
    }
