from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz  # PyMuPDF
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS para permitir acceso desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def extraer_texto_original(pdf_bytes: bytes) -> str:
    """
    Extrae solo la sección ORIGINAL del PDF (ignora DUPLICADO/TRIPLICADO).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    original_text = ""

    for page in doc:
        texto = page.get_text()
        if "ORIGINAL" in texto.upper() and not any(x in texto.upper() for x in ["DUPLICADO", "TRIPLICADO"]):
            original_text += texto
            break  # Solo tomamos el primer ORIGINAL

    return original_text

@app.post("/parse-and-send")
async def parse_and_send(pdfs: List[UploadFile] = File(...)):
    textos = []

    for pdf in pdfs:
        content = await pdf.read()
        texto_original = extraer_texto_original(content)
        textos.append(texto_original)

    texto_completo = "\n\n".join(textos)

    prompt = f"""
Te paso el texto de una factura. Extraé todos los datos clave del **receptor** (cliente de la factura), no del emisor.

Formato esperado (por cada factura):

{{
  "razon_social": "",
  "cuit": "",               ← CUIT del cliente
  "fecha": "",
  "condicion_iva": "",
  "domicilio": "",
  "importe_neto_gravado": 0.00,
  "iva": {{
    "21": 0.00,
    "27": 0.00,
    "10.5": 0.00,
    "5": 0.00,
    "2.5": 0.00,
    "0": 0.00
  }},
  "importe_otros_tributos": 0.00,
  "importe_total": 0.00,
  "detalle": [
    {{
      "producto_servicio": "",
      "cantidad": 0,
      "umedida": "",
      "precio_unit": 0.00,
      "subtotal": 0.00,
      "alicuota": "",
      "iva": 0.00,
      "subtotal_iva": 0.00
    }}
  ]
}}

Texto completo de la factura:
{texto_completo}
"""


    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}",
        json=payload
    )

    if response.status_code != 200:
        return {"error": "Fallo en Gemini", "detalle": response.text}

    resultado_raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    # Limpiar el bloque ```json ... ```
    json_limpio = re.search(r'\{.*\}|\[.*\]', resultado_raw, re.DOTALL)
    return {"resultado": json_limpio.group(0) if json_limpio else resultado_raw}
