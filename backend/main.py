from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from typing import List
import fitz  # PyMuPDF
from io import BytesIO
import pandas as pd
import asyncio
import traceback

from app.core.database import get_db, Base, engine
from app.utils.plantilla import get_json_plantilla
from app.utils.leer_qr import extraer_qr_desde_pdf
from app.utils.parsear_qr import extraer_datos_desde_qr_url
from app.utils.extraer_bs import extraer_datos_desde_texto
from app.utils.completar_llm import completar_con_llm, campos_incompletos
from app.routes import historial
from app.crud.historial import crear_historial

app = FastAPI()
app.include_router(historial.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
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

def es_factura_escaneada(pdf_bytes: bytes) -> bool:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto_total = ""
    imagenes_detectadas = 0
    for page in doc:
        texto_total += page.get_text().strip()
        imagenes_detectadas += len(page.get_images(full=True))
    print(f"🧪 Total de caracteres extraídos: {len(texto_total)}")
    print(f"🧪 Total de imágenes detectadas: {imagenes_detectadas}")
    return len(texto_total.strip()) < 50 and imagenes_detectadas > 0

@app.post("/procesar-excel")
async def procesar_excel(
    pdfs: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    filas = []

    async def procesar_pdf(pdf: UploadFile):
        try:
            content = await pdf.read()
            print(f"\n📄 Procesando archivo: {pdf.filename}")
            texto = ""

            if es_factura_escaneada(content):
                print("✅ Detectado como factura ESCANEADA")
                json_final = get_json_plantilla()
                factura = json_final["factura"]
                try:
                    factura = await completar_con_llm(factura, pdf_bytes=content)
                except Exception as e:
                    print(f"❌ Error al completar factura escaneada con Gemini: {e}")
            else:
                print("✅ Detectado como factura DIGITAL")
                texto = await asyncio.to_thread(extraer_texto_original, content)
                print("📝 Texto extraído:")
                print(texto)

                json_final = get_json_plantilla()
                factura = json_final["factura"]

                qr_url = extraer_qr_desde_pdf(content)
                if qr_url:
                    print(f"🔍 QR detectado: {qr_url}")
                    datos_qr = extraer_datos_desde_qr_url(qr_url)
                    print("📦 Datos extraídos del QR:")
                    print(datos_qr)
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

                datos_bs = await asyncio.to_thread(extraer_datos_desde_texto, texto)
                print("📁 Datos extraídos con regex:")
                print(datos_bs)

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
                print("⚠️ Campos incompletos. Enviando a Gemini...")
                try:
                    if texto.strip():
                        factura = await completar_con_llm(factura, texto=texto.strip())
                    else:
                        factura = await completar_con_llm(factura, pdf_bytes=content)
                except Exception as e:
                    print(f"❌ Error al completar con Gemini: {e}")

            crear_historial(db, nombre_pdf=pdf.filename, nombre_excel="facturas.xlsx")

            fila = {
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
            print(f"\n🧾 Agregando factura {len(filas)+1} al Excel...\n")
            filas.append(fila)

        except Exception:
            print("\n❌ Error inesperado procesando PDF:")
            traceback.print_exc()

    tareas = [procesar_pdf(pdf) for pdf in pdfs]
    await asyncio.gather(*tareas)

    print("📊 Generando archivo Excel consolidado...")
    df = pd.DataFrame(filas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Facturas")
    output.seek(0)

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=facturas.xlsx"})

Base.metadata.create_all(bind=engine)
