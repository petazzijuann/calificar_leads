import os
import json
import base64
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = [[
    "Timestamp",
    "Chat ID",
    "Usuario Telegram",
    "Mensaje Original",
    "Decisión",
    "Razonamiento",
    "Tiempo (s)",
]]

_service_cache = None


def _get_service():
    """
    Singleton del cliente de Google Sheets.
    Las credenciales se leen del env var GOOGLE_CREDENTIALS_JSON (base64 del JSON del Service Account).
    Se cachea para reutilizar entre invocaciones calientes en Vercel.
    """
    global _service_cache
    if _service_cache is not None:
        return _service_cache

    credentials_b64 = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    credentials_json = base64.b64decode(credentials_b64).decode("utf-8")
    credentials_dict = json.loads(credentials_json)

    creds = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=SCOPES,
    )

    # cache_discovery=False evita errores de escritura en el filesystem de Vercel
    _service_cache = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return _service_cache


def _ensure_tab(service, tab_name: str) -> None:
    """
    Verifica si la pestaña del mes ya existe.
    Si no existe, la crea con los headers correspondientes.
    """
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID
    ).execute()
    existing_tabs = [s["properties"]["title"] for s in spreadsheet["sheets"]]

    if tab_name in existing_tabs:
        return

    # Crear la pestaña nueva
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
    ).execute()

    # Agregar headers en la fila 1
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{tab_name}!A1:G1",
        valueInputOption="RAW",
        body={"values": HEADERS},
    ).execute()


def log_lead(chat_id: str, username: str, message: str, result: dict) -> None:
    """
    Registra el lead analizado en la pestaña del mes actual.
    El razonamiento siempre se guarda en español (campo razonamiento_es del LLM).
    Si la pestaña del mes no existe, se crea automáticamente.
    """
    service = _get_service()

    now = datetime.now()
    tab = now.strftime("%Y-%m")          # ej: "2026-05"
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    _ensure_tab(service, tab)

    # Razonamiento en español para el registro interno
    razonamiento_registro = result.get("razonamiento_es") or result.get("razonamiento", "")

    row = [[
        timestamp,
        str(chat_id),
        str(username or "Sin username"),
        str(message),
        str(result.get("decision", "")),
        str(razonamiento_registro),
        str(result.get("elapsed", "")),
    ]]

    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{tab}!A:G",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": row},
    ).execute()
