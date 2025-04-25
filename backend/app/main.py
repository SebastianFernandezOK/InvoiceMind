from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz  # PyMuPDF

from utils.plantilla import get_json_plantilla
from utils.leer_qr import extraer_qr_desde_pdf
from utils.parsear_qr import extraer_datos_desde_qr_url
from utils.extraer_bs import extraer_datos_desde_texto
from utils.extraer_bs_html import extraer_datos_desde_html
from utils.parsear_por_claves import parsear_por_claves

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

        # Etapa 2: Texto original
        texto = extraer_texto_original(content)
        texto_completo += texto + "\n\n"
        factura = json_final["factura"]

        # Etapa 3: BeautifulSoup desde HTML
        datos_html = extraer_datos_desde_html(content)
        if datos_html.get("items"):
            factura["items"] = datos_html["items"]
        factura["totales"]["importe_total"] = datos_html.get("importe_total", factura["totales"]["importe_total"])
        factura["totales"]["iva_21"] = datos_html.get("iva_21", factura["totales"]["iva_21"])
        factura["totales"]["importe_neto_gravado"] = datos_html.get("importe_neto_gravado", factura["totales"]["importe_neto_gravado"])

        # Etapa 4: Regex y patrones fijos
        datos_bs = extraer_datos_desde_texto(texto)
        factura["receptor"]["cuit"] = datos_bs.get("receptor_cuit", factura["receptor"]["cuit"])
        factura["receptor"]["razon_social"] = datos_bs.get("receptor_razon_social", factura["receptor"]["razon_social"])
        factura["receptor"]["domicilio_comercial"] = datos_bs.get("receptor_domicilio", factura["receptor"]["domicilio_comercial"])
        factura["emisor"]["domicilio_comercial"] = datos_bs.get("emisor_domicilio", factura["emisor"]["domicilio_comercial"])
        factura["fecha_vencimiento_pago"] = datos_bs.get("fecha_vencimiento_pago", factura["fecha_vencimiento_pago"])
        factura["periodo_facturado"]["desde"] = datos_bs.get("periodo_desde", factura["periodo_facturado"]["desde"])
        factura["periodo_facturado"]["hasta"] = datos_bs.get("periodo_hasta", factura["periodo_facturado"]["hasta"])
        if "items" in datos_bs:
            factura["items"] = datos_bs["items"]

        # Etapa 5: Contexto sin regex
        datos_contexto = parsear_por_claves(texto)
        factura["receptor"]["razon_social"] = datos_contexto.get("razon_social", factura["receptor"]["razon_social"])
        factura["receptor"]["cuit"] = datos_contexto.get("cuit", factura["receptor"]["cuit"])
        factura["receptor"]["domicilio_comercial"] = datos_contexto.get("domicilio", factura["receptor"]["domicilio_comercial"])
        factura["receptor"]["condicion_iva"] = datos_contexto.get("condicion_iva", factura["receptor"]["condicion_iva"])
        factura["receptor"]["condicion_venta"] = datos_contexto.get("condicion_venta", factura["receptor"]["condicion_venta"])
        factura["fecha_emision"] = datos_contexto.get("fecha_emision", factura["fecha_emision"])
        factura["fecha_vencimiento_pago"] = datos_contexto.get("fecha_vencimiento_pago", factura["fecha_vencimiento_pago"])
        factura["periodo_facturado"]["desde"] = datos_contexto.get("periodo_desde", factura["periodo_facturado"]["desde"])
        factura["periodo_facturado"]["hasta"] = datos_contexto.get("periodo_hasta", factura["periodo_facturado"]["hasta"])

        try:
            total_val = datos_contexto.get("importe_total")
            if total_val:
                factura["totales"]["importe_total"] = float(total_val.replace('.', '').replace(',', '.'))
        except:
            pass

    return {
        "json": json_final,
        "texto": texto_completo.strip()
    }
