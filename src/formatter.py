import html


# ─── Mensajes estáticos ───────────────────────────────────────────────────────

WELCOME_MESSAGE_TEMPLATE = (
    "👋 ¡Hola, <b>{nombre}</b>! Soy tu asistente de calificación de leads.\n\n"
    "📝 <b>¿Cómo funciona?</b>\n"
    "Escribime los datos de tu lead en texto libre, tal como los describirías a un colega. "
    "Por ejemplo:\n\n"
    "<i>\"Empresa de consultoría en Madrid, 12 empleados, están buscando automatizar "
    "su proceso de onboarding con IA. Hablaron con nosotros hace 3 días.\"</i>\n\n"
    "🎯 <b>Te digo si el lead es:</b>\n"
    "🟢 Calificado Alto — encaja perfecto con el ICP\n"
    "🟡 Calificado Medio — hay potencial pero con gaps\n"
    "🔴 No Calificado — no es el momento\n"
    "⚠️ Incompleto — te pido los datos que faltan\n\n"
    "¡Mandame tu primer lead cuando quieras!"
)

ONLY_TEXT_MESSAGE = (
    "📎 Solo proceso mensajes de texto. "
    "Escribime los datos del lead y lo analizo enseguida."
)

RATE_LIMIT_MESSAGE = (
    "⏳ Enviaste demasiados mensajes seguidos.\n"
    "Esperá un minuto y volvé a intentarlo."
)

ERROR_MESSAGE = (
    "❌ Ocurrió un error procesando tu mensaje. "
    "Intentá de nuevo en unos segundos."
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escapa caracteres HTML para evitar errores de parsing en Telegram."""
    return html.escape(str(text or ""))


def build_welcome(first_name: str) -> str:
    """Construye el mensaje de bienvenida personalizado con el nombre del usuario."""
    nombre = _esc(first_name) if first_name else "ahí"
    return WELCOME_MESSAGE_TEMPLATE.format(nombre=nombre)


# ─── Formateador principal ────────────────────────────────────────────────────

def format_telegram_response(result: dict) -> str:
    """
    Convierte el JSON del LLM en un mensaje formateado (HTML) para Telegram.
    El razonamiento ya viene en el idioma del usuario desde el LLM.
    """
    decision = result.get("decision", "")
    razonamiento = _esc(result.get("razonamiento", ""))
    datos_faltantes = _esc(result.get("datos_faltantes", ""))
    elapsed = result.get("elapsed", "")

    footer = f"\n\n<i>⏱ Analizado en {elapsed}s</i>" if elapsed else ""

    if decision == "CALIFICADO_ALTO":
        return (
            f"🟢 <b>Lead Calificado — ALTO</b>\n\n"
            f"📋 <b>Análisis:</b>\n{razonamiento}\n\n"
            f"✅ Este lead encaja con tu ICP. ¡Vale la pena avanzar!"
            f"{footer}"
        )

    if decision == "CALIFICADO_MEDIO":
        return (
            f"🟡 <b>Lead Calificado — MEDIO</b>\n\n"
            f"📋 <b>Análisis:</b>\n{razonamiento}\n\n"
            f"⚠️ Cumple la mayoría del ICP pero hay puntos a confirmar."
            f"{footer}"
        )

    if decision == "NO_CALIFICADO":
        return (
            f"🔴 <b>Lead No Calificado</b>\n\n"
            f"📋 <b>Análisis:</b>\n{razonamiento}\n\n"
            f"❌ Este lead no se ajusta a tu ICP actual."
            f"{footer}"
        )

    if decision == "INCOMPLETO":
        faltante_block = (
            f"\n\n❓ <b>Para calificarlo necesito saber:</b>\n{datos_faltantes}"
            if datos_faltantes
            else ""
        )
        return (
            f"⚠️ <b>Lead Incompleto</b>\n\n"
            f"📋 <b>Lo que pude analizar:</b>\n{razonamiento}"
            f"{faltante_block}\n\n"
            f"📩 Mandame más datos y lo analizo de nuevo."
            f"{footer}"
        )

    # Fallback por si el LLM devuelve algo inesperado
    return "❓ No pude procesar este lead. Intentá de nuevo."
