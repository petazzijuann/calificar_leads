import sys
import os
import traceback

# Agrega el root del proyecto al path para que los imports de src/ funcionen en Vercel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()  # No-op en Vercel (usa env vars nativas); útil para desarrollo local

from flask import Flask, request, Response

from src.telegram_client import send_message, send_processing_message
from src.openai_client import qualify_lead
from src.sheets_client import log_lead
from src.rate_limiter import check_rate_limit
from src.formatter import (
    build_welcome,
    format_telegram_response,
    ONLY_TEXT_MESSAGE,
    RATE_LIMIT_MESSAGE,
    ERROR_MESSAGE,
)

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")


@app.route("/api/webhook", methods=["POST"])
@app.route("/", methods=["POST"])
def webhook():
    chat_id = None  # necesario para el bloque de error final

    try:
        # ── 1. Validar secret token de Telegram ──────────────────────────────
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if WEBHOOK_SECRET and secret != WEBHOOK_SECRET:
            return Response("Unauthorized", status=401)

        data = request.get_json(force=True, silent=True)
        if not data:
            return Response("OK", status=200)

        message = data.get("message")
        if not message:
            return Response("OK", status=200)

        # ── 2. Extraer datos del mensaje ──────────────────────────────────────
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = (message.get("text") or "").strip()
        user = message.get("from", {})
        first_name = user.get("first_name", "")
        username = user.get("username") or first_name or "Sin nombre"

        if not chat_id:
            return Response("OK", status=200)

        # ── 3. Comando /start ─────────────────────────────────────────────────
        if text == "/start":
            send_message(chat_id, build_welcome(first_name))
            return Response("OK", status=200)

        # ── 4. Ignorar mensajes no-texto (fotos, audios, stickers, etc.) ─────
        if not text:
            send_message(chat_id, ONLY_TEXT_MESSAGE)
            return Response("OK", status=200)

        # ── 5. Rate limiting ──────────────────────────────────────────────────
        allowed, count = check_rate_limit(chat_id)
        if not allowed:
            send_message(chat_id, RATE_LIMIT_MESSAGE)
            return Response("OK", status=200)

        # ── 6. Feedback inmediato (UX crítico para el timeout de Vercel) ──────
        send_processing_message(chat_id)

        # ── 7. Calificar lead con GPT-4o-mini ─────────────────────────────────
        result = qualify_lead(text)

        # ── 8. Enviar respuesta formateada al usuario ─────────────────────────
        response_text = format_telegram_response(result)
        send_message(chat_id, response_text)

        # ── 9. Loguear en Google Sheets (fallo no-crítico) ────────────────────
        try:
            log_lead(chat_id, username, text, result)
        except Exception as sheets_err:
            # Si Sheets falla, el usuario ya recibió su respuesta → no bloqueamos
            print(f"[SHEETS ERROR] {sheets_err}")

        return Response("OK", status=200)

    except Exception:
        print(f"[WEBHOOK ERROR]\n{traceback.format_exc()}")
        if chat_id:
            try:
                send_message(chat_id, ERROR_MESSAGE)
            except Exception:
                pass
        # Siempre 200 a Telegram para que no reintente el mismo update
        return Response("OK", status=200)


# ── Desarrollo local ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
