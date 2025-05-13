from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import fitz  # PyMuPDF
import pandas as pd
from io import BytesIO
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

@app.post("/procesar-excel")
async def procesar_excel(pdfs: List[UploadFile] = File(...)):
    facturas_finales = []

    for pdf in pdfs:
        content = await pdf.read()
        json_final = get_json_plantilla()
        texto = extraer_texto_original(content)

        # QR
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

        # Texto con BS
        datos_bs = extraer_datos_desde_texto(texto)
        factura = json_final["factura"]
        factura["receptor"]["cuit"] = datos_bs.get("receptor_cuit", "")
        factura["receptor"]["razon_social"] = datos_bs.get("receptor_razon_social", "")
        factura["receptor"]["domicilio_comercial"] = datos_bs.get("receptor_domicilio", "")
        factura["emisor"]["razon_social"] = datos_bs.get("emisor_razon_social", "")
        factura["emisor"]["domicilio_comercial"] = datos_bs.get("emisor_domicilio", "")
        factura["fecha_vencimiento_pago"] = datos_bs.get("fecha_vencimiento_pago", "")
        factura["periodo_facturado"]["desde"] = datos_bs.get("periodo_desde", "")
        factura["periodo_facturado"]["hasta"] = datos_bs.get("periodo_hasta", "")
        factura["totales"]["importe_neto_gravado"] = datos_bs.get("importe_neto_gravado", None)
        factura["totales"]["iva_21"] = datos_bs.get("iva_21", None)
        factura["totales"]["importe_total"] = datos_bs.get("importe_total", "")

        if "items" in datos_bs:
            factura["items"] = datos_bs["items"]

        # LLM
        if campos_incompletos(factura):
            try:
                json_final["factura"] = completar_con_llm(factura, texto.strip())
            except Exception:
                pass

        facturas_finales.append(json_final["factura"])

    # Aplanar para Excel
    filas = []
    for f in facturas_finales:
        fila = {
            "tipo": f.get("tipo", ""),
            "codigo": f.get("codigo", ""),
            "punto_venta": f.get("punto_venta", ""),
            "numero_comprobante": f.get("numero_comprobante", ""),
            "fecha_emision": f.get("fecha_emision", ""),
            "fecha_vencimiento_pago": f.get("fecha_vencimiento_pago", ""),
            "emisor_cuit": f.get("emisor", {}).get("cuit", ""),
            "emisor_razon_social": f.get("emisor", {}).get("razon_social", ""),
            "emisor_domicilio": f.get("emisor", {}).get("domicilio_comercial", ""),
            "receptor_cuit": f.get("receptor", {}).get("cuit", ""),
            "receptor_razon_social": f.get("receptor", {}).get("razon_social", ""),
            "receptor_domicilio": f.get("receptor", {}).get("domicilio_comercial", ""),
            "importe_total": f.get("totales", {}).get("importe_total", 0),
            "iva_21": f.get("totales", {}).get("iva_21", 0),
            "neto_gravado": f.get("totales", {}).get("importe_neto_gravado", 0),
            "cae": f.get("cae", {}).get("numero", "")
        }
        filas.append(fila)

    df = pd.DataFrame(filas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
        "Content-Disposition": "attachment; filename=facturas.xlsx"
    })
