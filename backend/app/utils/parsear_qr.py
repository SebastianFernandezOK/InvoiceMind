import json
import base64
from urllib.parse import urlparse, parse_qs

def extraer_datos_desde_qr_url(qr_url: str) -> dict:
    try:
        parsed = urlparse(qr_url)
        query = parse_qs(parsed.query)
        payload_base64 = query.get("p", [""])[0]

        # Asegurar padding base64 válido
        padding = len(payload_base64) % 4
        if padding != 0:
            payload_base64 += '=' * (4 - padding)

        decoded_bytes = base64.b64decode(payload_base64)
        decoded_json = json.loads(decoded_bytes.decode("utf-8"))

        return {
            "tipo": str(decoded_json.get("tipoCmp", "")),
            "codigo": str(decoded_json.get("tipoCmp", "")),
            "punto_venta": str(decoded_json.get("ptoVta", "")),
            "numero_comprobante": str(decoded_json.get("nroCmp", "")),
            "fecha_emision": decoded_json.get("fecha", ""),
            "emisor_cuit": str(decoded_json.get("cuit", "")),
            "qr_completo": qr_url
        }

    except Exception as e:
        print(" Error al parsear QR:", e)
        return {}
