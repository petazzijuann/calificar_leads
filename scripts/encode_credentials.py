"""
Utilidad para codificar el JSON del Service Account de Google en base64.
Ese valor va como variable de entorno GOOGLE_CREDENTIALS_JSON en Vercel.

Uso:
    python scripts/encode_credentials.py ruta/al/credentials.json
"""

import sys
import base64


def encode_credentials(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/encode_credentials.py ruta/al/credentials.json")
        sys.exit(1)

    encoded = encode_credentials(sys.argv[1])

    print("\n✅ Credenciales codificadas correctamente.\n")
    print("Copiá este valor como GOOGLE_CREDENTIALS_JSON en Vercel y en tu .env:\n")
    print(encoded)
    print()
