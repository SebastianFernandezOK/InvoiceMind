import fitz  # PyMuPDF
import numpy as np
import cv2
from pyzbar.pyzbar import decode
from typing import Optional

def extraer_qr_desde_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Extrae el primer QR válido de un PDF (en bytes) que contenga la cadena de AFIP/ARCA.
    Devuelve el texto del QR si lo encuentra, o None si no hay QR válido.
    """
    print(" Intentando extraer QR del PDF...")
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        print(f" Error abriendo PDF: {e}")
        return None

    try:
        for page in doc:
            # Renderizamos la página como imagen
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")

            # Convertimos a imagen OpenCV
            np_img = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if image is None:
                print(" Error al decodificar la imagen de la página.")
                continue

            # Detectamos QRs en la imagen
            qr_codes = decode(image)
            todos_qr = []
            for qr in qr_codes:
                try:
                    qr_text = qr.data.decode("utf-8")
                    todos_qr.append(qr_text)
                except Exception as e:
                    print(f" Error decodificando QR: {e}")
            print(" QRs detectados:", todos_qr)

            for qr_text in todos_qr:
                if "fe/qr/?p=" in qr_text and ("afip.gob.ar" in qr_text or "arca.gob.ar" in qr_text):
                    print(" QR válido encontrado:", qr_text)
                    return qr_text
    finally:
        doc.close()

    print(" No se detectó ningún QR válido.")
    return None
