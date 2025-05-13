from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import fitz  # PyMuPDF
import csv
from io import StringIO
import base64
import json
from app.utils.plantilla import get_json_plantilla
from app.utils.leer_qr import extraer_qr_desde_pdf
from app.utils.parsear_qr import extraer_datos_desde_qr_url
from app.utils.extraer_bs import extraer_datos_desde_texto
from app.utils.completar_llm import completar_con_llm, campos_incompletos

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
    facturas = []
    textos = []
    for pdf in pdfs:
        content = await pdf.read()
        json_final = get_json_plantilla()
        texto = extraer_texto_original(content)
        textos.append(texto)

        qr_url = extraer_qr_desde_pdf(content)
        if qr_url:
            datos_qr = extraer_datos_desde_qr_url(qr_url)
            factura = json_final["factura"]
            factura.update({
                "tipo": datos_qr.get("tipo", ""),
                "codigo": datos_qr.get("codigo", ""),
                "punto_venta": datos_qr.get("punto_venta", ""),
                "numero_comprobante": datos_qr.get("numero_comprobante", ""),
                "fecha_emision": datos_qr.get("fecha_emision", ""),
                "emisor": {
                    **factura.get("emisor", {}),
                    "cuit": datos_qr.get("emisor_cuit", "")
                },
                "qr": {"contenido": datos_qr.get("qr_completo", "")}
            })

        datos_bs = extraer_datos_desde_texto(texto)
        factura = json_final["factura"]
        factura["receptor"]["cuit"] = datos_bs.get("receptor_cuit", "")
        factura["receptor"]["razon_social"] = datos_bs.get("receptor_razon_social", "")
        factura["receptor"]["domicilio_comercial"] = datos_bs.get("receptor_domicilio", "")
        factura["emisor"]["domicilio_comercial"] = datos_bs.get("emisor_domicilio", "")
        factura["fecha_vencimiento_pago"] = datos_bs.get("fecha_vencimiento_pago", "")
        factura["periodo_facturado"]["desde"] = datos_bs.get("periodo_desde", "")
        factura["periodo_facturado"]["hasta"] = datos_bs.get("periodo_hasta", "")
        factura["totales"]["importe_neto_gravado"] = datos_bs.get("importe_neto_gravado", None)
        factura["totales"]["iva_21"] = datos_bs.get("iva_21", None)
        factura["totales"]["importe_total"] = datos_bs.get("importe_total", "")

        if "items" in datos_bs:
            factura["items"] = datos_bs["items"]

        facturas.append(json_final)

    return {"facturas": facturas, "textos": textos}
@app.post("/completar-json-con-gemini")
async def completar_json_con_gemini(data: dict = Body(...)):
    try:
        json_incompleto = data.get("json")
        texto_factura = data.get("texto", "")

        if not json_incompleto or not texto_factura:
            return {"error": "Faltan campos 'json' o 'texto' en el body."}

        if not campos_incompletos(json_incompleto):
            return {"json": json_incompleto, "info": "No hay campos incompletos."}

        json_completado = completar_con_llm(json_incompleto, texto_factura.strip())

        # 🔍 Agregá este print para ver qué devuelve Gemini
        print("✅ JSON COMPLETADO:")
        print(json.dumps(json_completado, indent=2))

        return {"json": json_completado}

    except Exception as e:
        print("❌ ERROR en completar-json-con-gemini:", str(e))
        return {"error": f"Error procesando con Gemini: {str(e)}"}


import os


@app.post("/procesar-y-exportar-csv")
async def procesar_y_exportar_csv(pdfs: List[UploadFile] = File(...)):
    facturas_csv = []
    facturas_json = []
    headers_csv = set()

    for pdf in pdfs:
        content = await pdf.read()
        json_final = get_json_plantilla()
        texto = extraer_texto_original(content)

        qr_url = extraer_qr_desde_pdf(content)
        if qr_url:
            datos_qr = extraer_datos_desde_qr_url(qr_url)
            factura = json_final["factura"]
            factura.update({
                "tipo": datos_qr.get("tipo", ""),
                "codigo": datos_qr.get("codigo", ""),
                "punto_venta": datos_qr.get("punto_venta", ""),
                "numero_comprobante": datos_qr.get("numero_comprobante", ""),
                "fecha_emision": datos_qr.get("fecha_emision", ""),
                "emisor": {
                    **factura.get("emisor", {}),
                    "cuit": datos_qr.get("emisor_cuit", "")
                },
                "qr": {"contenido": datos_qr.get("qr_completo", "")}
            })

        datos_bs = extraer_datos_desde_texto(texto)
        factura = json_final["factura"]
        factura["receptor"]["cuit"] = datos_bs.get("receptor_cuit", "")
        factura["receptor"]["razon_social"] = datos_bs.get("receptor_razon_social", "")
        factura["receptor"]["domicilio_comercial"] = datos_bs.get("receptor_domicilio", "")
        factura["emisor"]["domicilio_comercial"] = datos_bs.get("emisor_domicilio", "")
        factura["fecha_vencimiento_pago"] = datos_bs.get("fecha_vencimiento_pago", "")
        factura["periodo_facturado"]["desde"] = datos_bs.get("periodo_desde", "")
        factura["periodo_facturado"]["hasta"] = datos_bs.get("periodo_hasta", "")
        factura["totales"]["importe_neto_gravado"] = datos_bs.get("importe_neto_gravado", None)
        factura["totales"]["iva_21"] = datos_bs.get("iva_21", None)
        factura["totales"]["importe_total"] = datos_bs.get("importe_total", "")

        if "items" in datos_bs:
            factura["items"] = datos_bs["items"]

        if campos_incompletos(json_final["factura"]):
            try:
                json_final["factura"] = completar_con_llm(json_final["factura"], texto.strip())
                json_final["_completada_por_gemini"] = True
            except Exception:
                json_final["_completada_por_gemini"] = False
        else:
            json_final["_completada_por_gemini"] = False

        facturas_json.append(json_final)

        flat_factura = {
            "fecha_emision": factura.get("fecha_emision", ""),
            "tipo": factura.get("tipo", ""),
            "codigo": factura.get("codigo", ""),
            "punto_venta": factura.get("punto_venta", ""),
            "numero_comprobante": factura.get("numero_comprobante", ""),
            "cuit_emisor": factura.get("emisor", {}).get("cuit", ""),
            "razon_emisor": factura.get("emisor", {}).get("razon_social", ""),
            "domicilio_emisor": factura.get("emisor", {}).get("domicilio_comercial", ""),
            "cuit_receptor": factura.get("receptor", {}).get("cuit", ""),
            "razon_receptor": factura.get("receptor", {}).get("razon_social", ""),
            "domicilio_receptor": factura.get("receptor", {}).get("domicilio_comercial", ""),
            "importe_total": factura.get("totales", {}).get("importe_total", ""),
            "iva_21": factura.get("totales", {}).get("iva_21", ""),
            "neto_gravado": factura.get("totales", {}).get("importe_neto_gravado", "")
        }

        facturas_csv.append(flat_factura)
        headers_csv.update(flat_factura.keys())

    # ✅ Usamos delimitador punto y coma
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=sorted(headers_csv), delimiter=';')
    writer.writeheader()
    writer.writerows(facturas_csv)
    csv_text = csv_buffer.getvalue()
    csv_base64 = base64.b64encode(csv_text.encode("utf-8")).decode("utf-8")

    return {
        "csv_text": csv_text,
        "csv_base64": csv_base64,
        "facturas": facturas_json
    }
