import io
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

def convertir_pdf_a_html(pdf_bytes: bytes) -> str:
    output = io.StringIO()
    laparams = LAParams()
    extract_text_to_fp(io.BytesIO(pdf_bytes), output, laparams=laparams, output_type="html", codec=None)
    return output.getvalue()


def extraer_datos_desde_html(pdf_bytes: bytes) -> dict:
    datos = {
        "items": [],
        "importe_total": None,
        "iva_21": None,
        "importe_neto_gravado": None
    }

    html = convertir_pdf_a_html(pdf_bytes)
    soup = BeautifulSoup(html, "html.parser")

    # 🔍 Buscar posibles tablas de ítems
    tablas = soup.find_all("table")

    for tabla in tablas:
        filas = tabla.find_all("tr")
        for fila in filas:
            columnas = [td.get_text(strip=True) for td in fila.find_all("td")]
            if len(columnas) >= 4:
                desc = columnas[0]
                cantidad = columnas[1].replace(",", ".")
                precio = columnas[2].replace(".", "").replace(",", ".")
                iva = columnas[3]

                try:
                    datos["items"].append({
                        "codigo": "",
                        "descripcion": desc,
                        "cantidad": float(cantidad),
                        "unidad_medida": "unidades",
                        "precio_unitario": float(precio),
                        "bonificacion": 0.0,
                        "subtotal": float(precio),
                        "alicuota_iva": iva,
                        "iva_monto": 0.0,  # Se puede calcular después
                        "subtotal_con_iva": 0.0
                    })
                except:
                    pass

    # 🔍 Buscar totales en texto
    textos = soup.find_all(text=True)
    for t in textos:
        line = t.strip().lower()
        if "importe total" in line:
            try:
                monto = line.split()[-1]
                datos["importe_total"] = float(monto.replace(".", "").replace(",", "."))
            except:
                pass
        elif "iva 21" in line:
            try:
                monto = line.split()[-1]
                datos["iva_21"] = float(monto.replace(".", "").replace(",", "."))
            except:
                pass
        elif "subtotal" in line or "neto gravado" in line:
            try:
                monto = line.split()[-1]
                datos["importe_neto_gravado"] = float(monto.replace(".", "").replace(",", "."))
            except:
                pass

    return datos
