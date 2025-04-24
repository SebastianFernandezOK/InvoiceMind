import re
from bs4 import BeautifulSoup

def extraer_datos_desde_texto(texto: str) -> dict:
    datos = {}

    # 🔍 Buscar CUITs
    cuit_list = re.findall(r"CUIT\s*:?\s*(\d{2}-?\d{8}-?\d)", texto)
    if len(cuit_list) > 1:
        datos["receptor_cuit"] = cuit_list[1]
        datos["emisor_cuit"] = cuit_list[0]
    elif len(cuit_list) == 1:
        datos["receptor_cuit"] = cuit_list[0]

    # 🏢 Buscar razón social del receptor
    razon_match = re.search(r"(Raz[oó]n Social|Cliente)\s*:?\s*(.+)", texto)
    if razon_match:
        razon = razon_match.group(2).strip()
        if razon and not razon.lower().startswith("domicilio"):
            datos["receptor_razon_social"] = razon

    # 🏠 Domicilio receptor (evitar fechas)
    domicilio_match = re.search(r"Domicilio(?: Comercial)?\s*:?\s*(.+)", texto)
    if domicilio_match:
        dom = domicilio_match.group(1).strip()
        if not re.match(r'\d{2}/\d{2}/\d{4}', dom):  # evitar capturar una fecha
            datos["receptor_domicilio"] = dom

    # 🏠 Domicilio emisor (más contexto)
    match_dom_emisor = re.search(r"(?:Jose|Av\.?|Calle)[^\n]{10,100},\s*[^\n]+", texto)
    if match_dom_emisor:
        datos["emisor_domicilio"] = match_dom_emisor.group(0).strip()

    # 📅 Fecha de vencimiento
    vencimiento = re.search(r"Vencimiento\s*:?\s*(\d{2}/\d{2}/\d{4})", texto)
    if vencimiento:
        datos["fecha_vencimiento_pago"] = vencimiento.group(1)

    # 📅 Periodo facturado
    periodo = re.search(r"Desde\s*(\d{2}/\d{2}/\d{4})\s*Hasta\s*(\d{2}/\d{2}/\d{4})", texto)
    if periodo:
        datos["periodo_desde"] = periodo.group(1)
        datos["periodo_hasta"] = periodo.group(2)

    # 💵 Totales
    total = re.search(r"Importe Total\s*\$?\s*([\d.,]+)", texto)
    if total:
        datos["importe_total"] = float(total.group(1).replace('.', '').replace(',', '.'))

    neto = re.search(r"(?:Subtotal|Importe Neto Gravado)\s*\$?\s*([\d.,]+)", texto)
    if neto:
        datos["importe_neto_gravado"] = float(neto.group(1).replace('.', '').replace(',', '.'))

    iva = re.search(r"IVA\s+21%\s*\$?\s*([\d.,]+)", texto)
    if iva:
        datos["iva_21"] = float(iva.group(1).replace('.', '').replace(',', '.'))

    # 📦 Ítems (generalizado)
    item_regex = re.search(
        r"(Servicio .+?)\s+(\d+,\d{2})\s+unidades\s+\$?([\d.,]+).*IVA\s+(\d+)%", texto, re.DOTALL
    )
    if item_regex:
        descripcion = item_regex.group(1).strip()
        cantidad = float(item_regex.group(2).replace(',', '.'))
        precio_unit = float(item_regex.group(3).replace('.', '').replace(',', '.'))
        alicuota = item_regex.group(4)
        subtotal = precio_unit
        iva_monto = round(subtotal * (float(alicuota)/100), 2)
        subtotal_iva = round(subtotal + iva_monto, 2)

        datos["items"] = [{
            "codigo": "",
            "descripcion": descripcion,
            "cantidad": cantidad,
            "unidad_medida": "unidades",
            "precio_unitario": precio_unit,
            "bonificacion": 0.0,
            "subtotal": subtotal,
            "alicuota_iva": f"{alicuota}%",
            "iva_monto": iva_monto,
            "subtotal_con_iva": subtotal_iva
        }]

    return datos
