from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz  # PyMuPDF

from backend.app.utils.plantilla import get_json_plantilla
from backend.app.utils.leer_qr import extraer_qr_desde_pdf
from backend.app.utils.parsear_qr import extraer_datos_desde_qr_url
from backend.app.utils.extraer_bs import extraer_datos_desde_texto

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["http://localhost:5173"]
)

def extraer_texto_original(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    original_text = ""

    for page in doc:
        texto = page.get_text()
        if "ORIGINAL" in texto.upper() and not any(x in texto.upper() for x in ["DUPLICADO", "TRIPLICADO"]):
            original_text += texto
            break

    return original_text

@app.post("/procesar-todo-local")
async def procesar_todo_local(pdfs: List[UploadFile] = File(...)):
    json_final = get_json_plantilla()
    texto_completo = ""

    for pdf in pdfs:
        content = await pdf.read()

        # Etapa 1: QR
        qr_url = extraer_qr_desde_pdf(content)
        if qr_url:
            datos_qr = extraer_datos_desde_qr_url(qr_url)
            factura = json_final["factura"]
            factura["tipo"] = datos_qr.get("tipo", "")
            factura["codigo"] = datos_qr.get("codigo", "")
            factura["punto_venta"] = datos_qr.get("punto_venta", "")
            factura["numero_comprobante"] = datos_qr.get("numero_comprobante", "")
            factura["fecha_emision"] = datos_qr.get("fecha_emision", "")
            factura["emisor"]["cuit"] = datos_qr.get("emisor_cuit", "")
            factura["qr"] = {"contenido": datos_qr.get("qr_completo", "")}

        # Etapa 2: texto original
        texto = extraer_texto_original(content)
        texto_completo += texto + "\n\n"

        # Etapa 3: análisis con BeautifulSoup y regex
        datos_bs = extraer_datos_desde_texto(texto)
        factura = json_final["factura"]

        # Receptor
        factura["receptor"]["cuit"] = datos_bs.get("receptor_cuit", factura["receptor"]["cuit"])
        factura["receptor"]["razon_social"] = datos_bs.get("receptor_razon_social", factura["receptor"]["razon_social"])
        factura["receptor"]["domicilio_comercial"] = datos_bs.get("receptor_domicilio", factura["receptor"]["domicilio_comercial"])

        # Emisor
        factura["emisor"]["domicilio_comercial"] = datos_bs.get("emisor_domicilio", factura["emisor"]["domicilio_comercial"])

        # Fechas
        factura["fecha_vencimiento_pago"] = datos_bs.get("fecha_vencimiento_pago", "")
        factura["periodo_facturado"]["desde"] = datos_bs.get("periodo_desde", "")
        factura["periodo_facturado"]["hasta"] = datos_bs.get("periodo_hasta", "")

        # Totales
        factura["totales"]["importe_neto_gravado"] = datos_bs.get("importe_neto_gravado", None)
        factura["totales"]["iva_21"] = datos_bs.get("iva_21", None)
        factura["totales"]["importe_total"] = datos_bs.get("importe_total", factura["totales"]["importe_total"])

        # Ítems
        if "items" in datos_bs:
            factura["items"] = datos_bs["items"]

    return {
        "json": json_final,
        "texto": texto_completo.strip()
    }
