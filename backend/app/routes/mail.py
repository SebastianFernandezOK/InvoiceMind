import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
import pandas as pd
from io import BytesIO
import asyncio
import traceback
from app.utils.plantilla import get_json_plantilla
from app.utils.leer_qr import extraer_qr_desde_pdf
from app.utils.parsear_qr import extraer_datos_desde_qr_url
from app.utils.extraer_bs import extraer_datos_desde_texto
from app.utils.completar_llm import completar_con_llm, campos_incompletos
from app.crud.historial import crear_historial
from app.utils.procesar_facturas import procesar_lote_facturas
from app.utils.procesar_facturas import procesar_factura_pdf


router = APIRouter()

def enviar_email_con_excel(archivo_excel, destinatario_email):
    msg = MIMEMultipart()
    msg['From'] = "procesadorfacturas@gmail.com"
    msg['To'] = destinatario_email
    msg['Subject'] = "Factura procesada - Excel adjunto"
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(archivo_excel)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename=facturas.xlsx")
    msg.attach(part)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("procesadorfacturas@gmail.com", "odxa sxyq rucg htnf")
        text = msg.as_string()
        server.sendmail(msg['From'], msg['To'], text)
        server.quit()
        print(f"Correo enviado a {destinatario_email}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

@router.post("/procesar-email")
async def procesar_email(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    remitente = data.get("from")
    archivos = data.get("attachments", [])
    user = db.query(User).filter(User.email == remitente).first()
    if not user:
        raise HTTPException(status_code=403, detail="Usuario no registrado")
    class FakeUploadFile:
        def __init__(self, filename, content):
            self.filename = filename
            self._content = content
        async def read(self):
            return self._content
    pdfs = [FakeUploadFile(a["filename"], bytes(a["content"])) for a in archivos]
    filas = await procesar_lote_facturas(pdfs, db=db, user_email=remitente)
    df = pd.DataFrame(filas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Facturas")
    output.seek(0)
    enviar_email_con_excel(output.getvalue(), remitente)
    return {"msg": "Facturas procesadas y Excel enviado"}
