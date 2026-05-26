import os
import json
import time
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

ICP_DEFINITION = os.environ.get(
    "ICP_DEFINITION",
    "Empresa de servicios o consultoría B2B, con mínimo 5 empleados, "
    "ubicada en España o Latinoamérica, con interés declarado o implícito "
    "en automatización de procesos o inteligencia artificial.",
)

SYSTEM_PROMPT = """Eres un asistente experto en calificación de leads B2B para un equipo comercial.

ICP (Ideal Customer Profile) de referencia:
{icp}

Tu tarea es analizar el texto libre que describe un lead y clasificarlo en UNA de estas categorías:

- CALIFICADO_ALTO: Cumple todos los criterios del ICP de forma clara y explícita.
- CALIFICADO_MEDIO: Cumple la mayoría de los criterios pero hay gaps o información incierta.
- NO_CALIFICADO: Claramente no cumple el ICP (sector incorrecto, tamaño incorrecto, fuera de geografía).
- INCOMPLETO: Falta información esencial para evaluar correctamente el lead.

REGLAS ESTRICTAS:
1. Si el mensaje NO menciona el número de empleados o tamaño del equipo → decisión INCOMPLETO, sin excepciones.
2. Detecta el idioma del mensaje del usuario y usa ese mismo idioma en los campos "razonamiento" y "datos_faltantes".
3. El campo "razonamiento_es" SIEMPRE debe estar escrito en español (es el registro interno).
4. Sé específico con los datos concretos del lead. Nunca respondas de forma genérica.
5. Máximo 80 palabras por campo de razonamiento.

Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, con esta estructura exacta:
{{
  "decision": "CALIFICADO_ALTO|CALIFICADO_MEDIO|NO_CALIFICADO|INCOMPLETO",
  "razonamiento": "2-3 líneas en el idioma del usuario, mencionando datos específicos del lead",
  "datos_faltantes": "solo si es INCOMPLETO: qué información concreta falta, en el idioma del usuario",
  "razonamiento_es": "el mismo razonamiento traducido al español para el registro interno",
  "idioma": "es|en|pt|fr|de|etc"
}}"""


def qualify_lead(message_text: str) -> dict:
    """
    Llama a GPT-4o-mini con el texto del lead y retorna un dict con la decisión,
    razonamiento, y metadata (idioma, elapsed time).
    """
    start_time = time.time()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(icp=ICP_DEFINITION),
            },
            {
                "role": "user",
                "content": f"Lead a calificar:\n\n{message_text}",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=350,
        temperature=0.2,  # Bajo para respuestas consistentes y reproducibles
    )

    elapsed = round(time.time() - start_time, 2)
    result = json.loads(response.choices[0].message.content)
    result["elapsed"] = elapsed
    return result
