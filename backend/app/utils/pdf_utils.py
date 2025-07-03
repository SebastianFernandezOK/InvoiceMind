import fitz

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
