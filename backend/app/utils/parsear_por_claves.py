import re

def parsear_por_claves(texto: str) -> dict:
    lineas = [line.strip() for line in texto.splitlines() if line.strip()]
    resultado = {}
    cuit_list = []

    for i, linea in enumerate(lineas):
        linea_lc = linea.lower()

        # CUIT (extraemos todos, y descartamos el primero si ya está como emisor)
        match_cuit = re.search(r"\d{2}-?\d{8}-?\d", linea)
        if match_cuit:
            cuit = match_cuit.group()
            cuit_list.append(cuit)

        # Fechas con formato dd/mm/yyyy
        if "fecha de emisión" in linea_lc or "fecha emisión" in linea_lc:
            match = re.search(r"\d{2}/\d{2}/\d{4}", linea)
            if match:
                resultado["fecha_emision"] = match.group()
        elif "vencimiento" in linea_lc:
            match = re.search(r"\d{2}/\d{2}/\d{4}", linea)
            if match:
                resultado["fecha_vencimiento_pago"] = match.group()
        elif "desde" in linea_lc and "hasta" in linea_lc:
            fechas = re.findall(r"\d{2}/\d{2}/\d{4}", linea)
            if len(fechas) == 2:
                resultado["periodo_desde"] = fechas[0]
                resultado["periodo_hasta"] = fechas[1]

        # Importe total
        if "importe total" in linea_lc or "total a pagar" in linea_lc or "total:" in linea_lc:
            match = re.search(r"\d{1,3}(?:\.\d{3})*(?:,\d{2})", linea)
            if match:
                resultado["importe_total"] = match.group()

        # Detección básica por etiquetas conocidas
        if any(key in linea_lc for key in ["razón social", "nombre", "cliente"]):
            valor = linea.split(":", 1)[-1].strip() if ":" in linea else ""
            if valor:
                resultado["razon_social"] = valor
            elif i + 1 < len(lineas):
                resultado["razon_social"] = lineas[i + 1].strip()

        if "condición iva" in linea_lc or "responsable" in linea_lc:
            resultado["condicion_iva"] = linea.split(":")[-1].strip()

        if "condición de venta" in linea_lc or "forma de pago" in linea_lc:
            resultado["condicion_venta"] = linea.split(":")[-1].strip()

        if "domicilio" in linea_lc or "dirección" in linea_lc:
            if ":" in linea:
                valor = linea.split(":", 1)[-1].strip()
                if valor and not valor.lower().startswith("condición"):
                    resultado["domicilio"] = valor
            elif i + 1 < len(lineas):
                candidato = lineas[i + 1].strip()
                if len(candidato) > 6 and not candidato.lower().startswith("condición"):
                    resultado["domicilio"] = candidato

    # Reglas de resolución de CUIT
    if len(cuit_list) >= 2:
        resultado["cuit"] = cuit_list[1]  # asumimos el segundo es el del receptor
    elif len(cuit_list) == 1:
        resultado["cuit"] = cuit_list[0]

    return resultado
