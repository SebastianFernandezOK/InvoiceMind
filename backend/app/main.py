from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from typing import List
import fitz  # PyMuPDF
from io import BytesIO
import pandas as pd
import asyncio

from app.core.database import get_db
from app.utils.plantilla import get_json_plantilla
from app.utils.leer_qr import extraer_qr_desde_pdf
from app.utils.parsear_qr import extraer_datos_desde_qr_url
from app.utils.extraer_bs import extraer_datos_desde_texto
from app.utils.completar_llm import completar_con_llm, campos_incompletos
from app.routes import historial
from app.crud.historial import crear_historial
from app.core.database import Base, engine


app = FastAPI()
app.include_router(historial.router)

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
async def procesar_excel(
    pdfs: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    resultados = []

    async def procesar_pdf(pdf: UploadFile):
        content = await pdf.read()
        texto = extraer_texto_original(content)

        json_final = get_json_plantilla()
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

        if campos_incompletos(factura):
            try:
                factura_completa = await completar_con_llm(factura, texto.strip())
                factura = factura_completa
            except Exception:
                pass

        # Guardar historial
        crear_historial(db, nombre_pdf=pdf.filename, nombre_excel="facturas.xlsx")

        return factura

    tareas = [procesar_pdf(pdf) for pdf in pdfs]
    facturas = await asyncio.gather(*tareas)

    filas = []
    for f in facturas:
        row = {
            "fecha_emision": f.get("fecha_emision", ""),
            "tipo": f.get("tipo", ""),
            "codigo": f.get("codigo", ""),
            "punto_venta": f.get("punto_venta", ""),
            "numero_comprobante": f.get("numero_comprobante", ""),
            "cuit_emisor": f.get("emisor", {}).get("cuit", ""),
            "razon_emisor": f.get("emisor", {}).get("razon_social", ""),
            "domicilio_emisor": f.get("emisor", {}).get("domicilio_comercial", ""),
            "cuit_receptor": f.get("receptor", {}).get("cuit", ""),
            "razon_receptor": f.get("receptor", {}).get("razon_social", ""),
            "domicilio_receptor": f.get("receptor", {}).get("domicilio_comercial", ""),
            "importe_total": f.get("totales", {}).get("importe_total", ""),
            "iva_21": f.get("totales", {}).get("iva_21", ""),
            "neto_gravado": f.get("totales", {}).get("importe_neto_gravado", "")
        }
        filas.append(row)

    df = pd.DataFrame(filas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Facturas")
    output.seek(0)

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=facturas.xlsx"})
Base.metadata.create_all(bind=engine)
