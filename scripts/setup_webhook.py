"""
Script para registrar el webhook de Telegram apuntando a la URL de Vercel.
Ejecutar UNA VEZ después de cada deploy.

Uso:
    python scripts/setup_webhook.py

Requiere las variables de entorno TELEGRAM_BOT_TOKEN y TELEGRAM_WEBHOOK_SECRET
(podés cargar el .env antes de correrlo).
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN no está definido. Revisá tu .env")
    exit(1)


def set_webhook(vercel_url: str) -> None:
    webhook_url = f"{vercel_url.rstrip('/')}/api/webhook"
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

    payload = {
        "url": webhook_url,
        "allowed_updates": ["message"],
        "drop_pending_updates": True,  # Ignora mensajes acumulados durante el deploy
    }

    if WEBHOOK_SECRET:
        payload["secret_token"] = WEBHOOK_SECRET

    print(f"\n🔗 Registrando webhook en: {webhook_url}\n")

    response = httpx.post(api_url, json=payload, timeout=10)
    result = response.json()

    if result.get("ok"):
        print("✅ Webhook registrado correctamente.")
        print(f"   Respuesta: {result.get('description', '')}")
    else:
        print(f"❌ Error al registrar webhook: {result}")


def get_webhook_info() -> None:
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = httpx.get(api_url, timeout=10)
    info = response.json().get("result", {})
    print(f"\n📡 Estado actual del webhook:")
    print(f"   URL: {info.get('url', 'No configurado')}")
    print(f"   Pending updates: {info.get('pending_update_count', 0)}")
    if info.get("last_error_message"):
        print(f"   Último error: {info.get('last_error_message')}")


if __name__ == "__main__":
    vercel_url = input(
        "Ingresá la URL de tu proyecto en Vercel (ej: https://calificar-leads-bot.vercel.app): "
    ).strip()

    if not vercel_url.startswith("https://"):
        print("❌ La URL debe empezar con https://")
        exit(1)

    set_webhook(vercel_url)
    get_webhook_info()
