import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_notification(message: str, silent: bool = False):
    """Send a Telegram message to yourself."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":              TELEGRAM_CHAT_ID,
        "text":                 message,
        "parse_mode":           "HTML",          # supports <b>, <i>, <code>
        "disable_notification": silent,          # True = no sound/vibration
    }
    response = requests.post(url, data=payload)
    return response.json()