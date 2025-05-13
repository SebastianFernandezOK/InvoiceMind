import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


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

def completar_con_llm(json_final: dict, texto: str) -> dict:
    prompt = f"""
Sos un asistente experto en facturación electrónica en Argentina. Vas a recibir:

- Un texto completo extraído de una factura
- Un JSON con datos incompletos o incorrectos

Tu tarea es:
1. Leer el texto y analizarlo.
2. Rellenar todos los campos faltantes en el JSON.
3. Corregir cualquier campo mal escrito, incompleto o inválido.
4. **Responder solamente con el JSON corregido, en formato JSON plano. No uses comillas triples ni bloques de código.**

⚠️ No agregues comentarios, ni encabezados, ni texto adicional. Solo el JSON limpio.

Texto extraído:
{texto}

JSON parcial:
{json.dumps(json_final, indent=2)}
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            top_p=1,
            top_k=40,
            max_output_tokens=1024
        )
    )

    content = response.text.strip()
    print("🟡 Contenido devuelto por Gemini:")
    print(content)

    # Eliminar envoltorios tipo ```json ... ```
    match = re.search(r"```json(.*?)```", content, re.DOTALL)
    if match:
        content = match.group(1).strip()

    try:
        result = json.loads(content)
        print("✅ JSON válido extraído:")
        print(json.dumps(result, indent=2))
        return result
    except json.JSONDecodeError as e:
        print("❌ JSON inválido recibido de Gemini:")
        print(content)
        raise ValueError(f"Respuesta inválida de Gemini: {e}")
