import fitz  # PyMuPDF
import numpy as np
import cv2
from pyzbar.pyzbar import decode

def extraer_qr_desde_pdf(pdf_bytes: bytes) -> str:
    print(" Intentando extraer QR del PDF...")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        # Renderizamos la página como imagen
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")

        # Convertimos a imagen OpenCV
        np_img = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Detectamos QRs en la imagen
        qr_codes = decode(image)
        todos_qr = [qr.data.decode("utf-8") for qr in qr_codes]
        print(" QRs detectados:", todos_qr)

        for qr_text in todos_qr:
            if "fe/qr/?p=" in qr_text and ("afip.gob.ar" in qr_text or "arca.gob.ar" in qr_text):
                print(" QR válido encontrado:", qr_text)
                return qr_text

    print(" No se detectó ningún QR válido.")
    return ""
