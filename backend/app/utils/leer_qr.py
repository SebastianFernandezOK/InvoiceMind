import fitz  # PyMuPDF
import numpy as np
import cv2

def extraer_qr_desde_pdf(pdf_bytes: bytes) -> str:
    print("🔍 Intentando extraer QR del PDF...")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    detector = cv2.QRCodeDetector()

    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")

        # Convertir imagen a formato OpenCV
        np_img = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Detectar y decodificar QR
        data, bbox, _ = detector.detectAndDecode(image)

        if data:
            print("🧪 QR detectado:", data)
            if "fe/qr/?p=" in data and ("afip.gob.ar" in data or "arca.gob.ar" in data):
                print("✅ QR válido encontrado:", data)
                return data

    print("❌ No se detectó ningún QR válido.")
    return ""
