from fastapi import FastAPI, UploadFile, File, Depends, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse

from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import asyncio
import traceback
from io import BytesIO
import os

from app.core.database import get_db, Base, engine
from app.utils.plantilla import get_json_plantilla
from app.utils.leer_qr import extraer_qr_desde_pdf
from app.utils.parsear_qr import extraer_datos_desde_qr_url
from app.utils.extraer_bs import extraer_datos_desde_texto
from app.utils.completar_llm import completar_con_llm, campos_incompletos
from app.routes import historial
from app.routes import historial_excel
from app.crud.historial import crear_historial
from app.crud.historial_excel import crear_historial_excel
from app.routes import auth
from app.routes.mail import router as mail_router
from app.models.user import User
from app.utils.procesar_facturas import procesar_lote_facturas
from app.utils.pdf_utils import es_factura_escaneada, extraer_texto_original
from app.utils.mail_watcher import main_loop as mail_watcher_main_loop
from app.models.historial_archivo import HistorialArchivo
from app.models.historial_excel import HistorialExcel
from app.routes.auth import get_current_user

app = FastAPI()
app.include_router(historial.router)
app.include_router(historial_excel.router)
app.include_router(auth.router)
app.include_router(mail_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
)

@app.post("/procesar-excel")
async def procesar_excel(
    pdfs: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user_email: str = None,
    current_user: User = Depends(get_current_user)
):
    # Verificar si el usuario tiene procesamientos restantes
    if current_user.procesamientos_restantes <= 0:
        raise HTTPException(
            status_code=403, 
            detail=f"Has agotado tu límite de procesamientos. Plan actual: {current_user.plan.title()}"
        )
    
    # Verificar si tiene suficientes procesamientos para todos los PDFs
    num_pdfs = len(pdfs)
    if current_user.procesamientos_restantes < num_pdfs:
        raise HTTPException(
            status_code=403, 
            detail=f"No tienes suficientes procesamientos. Necesitas {num_pdfs}, tienes {current_user.procesamientos_restantes}"
        )
    
    filas = await procesar_lote_facturas(pdfs, db=db, user_email=user_email, user_id=current_user.id)
    
    # Descontar procesamientos realizados
    current_user.procesamientos_restantes -= num_pdfs
    db.commit()
    
    df = pd.DataFrame(filas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Facturas")
    output.seek(0)
    
    # Guardar el Excel en el historial
    excel_data = output.getvalue()
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_excel = f"facturas_{timestamp}.xlsx"
    
    crear_historial_excel(
        db=db,
        nombre_archivo=nombre_excel,
        user_id=current_user.id,
        cantidad_facturas=num_pdfs,
        excel_data=excel_data
    )
    
    # Resetear el buffer para la respuesta
    output.seek(0)
    
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={nombre_excel}"})

@app.get("/archivos/{nombre_pdf}")
def servir_pdf(nombre_pdf: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    registro = db.query(HistorialArchivo).filter(
        HistorialArchivo.nombre_pdf == nombre_pdf,
        HistorialArchivo.user_id == current_user.id  # Solo archivos del usuario actual
    ).first()
    if not registro or not registro.pdf_data:
        return Response(content="Archivo no encontrado", status_code=404)
    return Response(content=registro.pdf_data, media_type="application/pdf")

# El watcher de mails se lanza como tarea en el mismo event loop de FastAPI
@app.on_event("startup")
async def start_mail_watcher():
    asyncio.create_task(mail_watcher_main_loop())

# Crear las tablas automáticamente al iniciar el backend
Base.metadata.create_all(bind=engine)

