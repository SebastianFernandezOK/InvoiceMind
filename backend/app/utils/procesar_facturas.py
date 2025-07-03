import asyncio
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.user import User
from app.crud.historial import crear_historial
from app.utils.plantilla import get_json_plantilla
from app.utils.leer_qr import extraer_qr_desde_pdf
from app.utils.parsear_qr import extraer_datos_desde_qr_url
from app.utils.extraer_bs import extraer_datos_desde_texto
from app.utils.completar_llm import completar_con_llm, campos_incompletos
from app.utils.pdf_utils import es_factura_escaneada, extraer_texto_original
import traceback

async def procesar_factura_pdf(pdf, db: Optional[Session] = None, user_email: Optional[str] = None, user_id: Optional[int] = None):
    try:
        content = await pdf.read()
        texto = ""
        if es_factura_escaneada(content):
            json_final = get_json_plantilla()
            factura = json_final["factura"]
            try:
                factura = await completar_con_llm(factura, pdf_bytes=content)
            except Exception as e:
                print(f"Error LLM escaneada: {e}")
        else:
            texto = await asyncio.to_thread(extraer_texto_original, content)
            json_final = get_json_plantilla()
            factura = json_final["factura"]
            qr_url = extraer_qr_desde_pdf(content)
            if qr_url:
                datos_qr = extraer_datos_desde_qr_url(qr_url)
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
                if texto.strip():
                    factura = await completar_con_llm(factura, texto=texto.strip())
                else:
                    factura = await completar_con_llm(factura, pdf_bytes=content)
            except Exception as e:
                print(f"Error LLM: {e}")
        if db is not None and user_id is not None:
            # Guardar el PDF binario en el historial asociado al usuario
            crear_historial(db, nombre_pdf=getattr(pdf, 'filename', 'sin_nombre'), user_id=user_id, nombre_excel="facturas.xlsx", pdf_data=content)
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
        return fila
    except Exception:
        print("Error procesando PDF:")
        traceback.print_exc()
        return None

async def procesar_lote_facturas(pdfs: List, db: Optional[Session] = None, user_email: Optional[str] = None, user_id: Optional[int] = None):
    filas = []
    tareas = [procesar_factura_pdf(pdf, db=db, user_email=user_email, user_id=user_id) for pdf in pdfs]
    resultados = await asyncio.gather(*tareas)
    for fila in resultados:
        if fila:
            filas.append(fila)
    return filas
