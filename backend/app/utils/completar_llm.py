import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# ✅ Carga .env desde la raíz del proyecto, sin importar desde dónde se ejecute uvicorn
dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# 🧪 DEBUG: verificar si la API key se carga correctamente
print("🔑 GEMINI_API_KEY (debug):", os.getenv("GEMINI_API_KEY"))

# Configurar el modelo
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 🔍 Verifica si hay campos vacíos en el JSON
def campos_incompletos(data: dict) -> bool:
    def is_empty(val):
        return val in [None, "", [], {}]
    for v in data.values():
        if isinstance(v, dict):
            if campos_incompletos(v):
                return True
        elif is_empty(v):
            return True
    return False

# ✅ Función principal para completar datos faltantes usando Gemini
async def completar_con_llm(json_final: dict, texto: str = None, pdf_bytes: bytes = None) -> dict:
    if pdf_bytes:
        prompt = f"""
Este es un archivo PDF escaneado de una factura. Extraé todos los datos relevantes y devolvé un JSON que respete exactamente esta plantilla (usá español en los campos y no inventes nada):

Plantilla:
{json.dumps(json_final, indent=2)}

⚠️ No agregues comentarios, encabezados ni explicaciones. Solo devolvé el JSON limpio.
"""
        response = await model.generate_content_async(
            [prompt, {"mime_type": "application/pdf", "data": pdf_bytes}]
        )
        content = response.text.strip()

    elif texto:
        prompt = f"""
Sos un asistente experto en facturación electrónica en Argentina. Vas a recibir:

- Un texto completo extraído de una factura
- Un JSON con datos incompletos o incorrectos

Tu tarea es:
1. Leer el texto y analizarlo.
2. Rellenar todos los campos faltantes en el JSON.
3. Corregir cualquier campo mal escrito, incompleto o inválido.
4. **Responder solamente con el JSON corregido. No expliques nada.**

⚠️ No agregues comentarios, ni encabezados, ni texto adicional. Solo el JSON limpio.

Texto extraído:
\"\"\"{texto}\"\"\"

JSON parcial:
{json.dumps(json_final, indent=2)}
"""
        response = await model.generate_content_async(prompt)
        content = response.text.strip()
    else:
        raise ValueError("Debes proporcionar 'texto' o 'pdf_bytes'.")

    print("🟡 Gemini respondió:")
    print(content)

    # 🧼 Limpieza del contenido por si viene entre ```json ... ```
    match = re.search(r"```json(.*?)```", content, re.DOTALL)
    if match:
        content = match.group(1).strip()

    try:
        result = json.loads(content)
        print("✅ JSON parseado correctamente.")
        return result
    except json.JSONDecodeError as e:
        print("❌ Error: JSON inválido")
        print(content)
        raise ValueError(f"Respuesta inválida de Gemini: {e}")

# ✅ Alias para flujo de facturas escaneadas
async def completar_factura_escaneada(json_final: dict, pdf_bytes: bytes) -> dict:
    return await completar_con_llm(json_final=json_final, pdf_bytes=pdf_bytes)
