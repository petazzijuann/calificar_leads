import os
import httpx

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
TIMEOUT = 8  # seconds


def send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> dict:
    """Envía un mensaje a un chat de Telegram."""
    url = f"{API_BASE}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    try:
        response = httpx.post(url, json=payload, timeout=TIMEOUT)
        return response.json()
    except Exception as e:
        print(f"[TELEGRAM ERROR] send_message: {e}")
        return {}


def send_processing_message(chat_id: str) -> dict:
    """Envía el mensaje inmediato de 'Analizando...' para dar feedback rápido."""
    return send_message(chat_id, "⏳ <b>Analizando tu lead...</b>")
