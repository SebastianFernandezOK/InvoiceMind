import imaplib
import email
from email.header import decode_header
import time
import os
from app.utils.procesar_facturas import procesar_lote_facturas
from app.routes.mail import enviar_email_con_excel
from io import BytesIO
import pandas as pd
import asyncio
from app.core.database import SessionLocal  # Importar SessionLocal para crear sesiones DB

# Configuración
IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = os.environ.get('MAIL_USER', 'procesadorfacturas@gmail.com')
EMAIL_PASSWORD = os.environ.get('MAIL_PASS', 'odxa sxyq rucg htnf')
CHECK_INTERVAL = 5  # segundos

# Conexión IMAP

def connect_mailbox():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select('inbox')
    return mail

def fetch_unread_mails(mail):
    status, messages = mail.search(None, '(UNSEEN)')
    if status != 'OK':
        return []
    return messages[0].split()

def get_attachments_from_msg(msg):
    attachments = []
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if filename and filename.lower().endswith('.pdf'):
            data = part.get_payload(decode=True)
            attachments.append({'filename': filename, 'content': data})
    return attachments

async def process_mail_and_respond(mail, num):
    status, data = mail.fetch(num, '(RFC822)')
    if status != 'OK':
        return
    msg = email.message_from_bytes(data[0][1])
    remitente = email.utils.parseaddr(msg['From'])[1]
    attachments = get_attachments_from_msg(msg)
    if not attachments:
        print(f"No hay PDFs en el mail de {remitente}")
        return
    class FakeUploadFile:
        def __init__(self, filename, content):
            self.filename = filename
            self._content = content
        async def read(self):
            return self._content
    pdfs = [FakeUploadFile(a['filename'], a['content']) for a in attachments]
    # Crear sesión DB y pasarla a procesar_lote_facturas
    db = SessionLocal()
    try:
        filas = await procesar_lote_facturas(pdfs, db=db, user_email=remitente)
        df = pd.DataFrame(filas)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Facturas")
        output.seek(0)
        enviar_email_con_excel(output.getvalue(), remitente)
        print(f"Procesado y respondido a {remitente}")
    finally:
        db.close()

async def main_loop():
    while True:
        try:
            mail = connect_mailbox()
            unread = fetch_unread_mails(mail)
            if unread:
                print(f"Encontrados {len(unread)} mails no leídos")
            for num in unread:
                await process_mail_and_respond(mail, num)
                # Marcar como leído
                mail.store(num, '+FLAGS', '\\Seen')
            mail.logout()
        except Exception as e:
            print(f"Error en el watcher: {e}")
        await asyncio.sleep(CHECK_INTERVAL)  

if __name__ == "__main__":
    asyncio.run(main_loop())
