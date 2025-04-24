def get_json_plantilla():
    return {
        "factura": {
            "tipo": "",
            "codigo": "",
            "punto_venta": "",
            "numero_comprobante": "",
            "fecha_emision": "",
            "fecha_vencimiento_pago": "",
            "periodo_facturado": {
                "desde": "",
                "hasta": ""
            },
            "emisor": {
                "razon_social": "",
                "domicilio_comercial": "",
                "cuit": "",
                "ingresos_brutos": "",
                "fecha_inicio_actividades": "",
                "condicion_iva": ""
            },
            "receptor": {
                "razon_social": "",
                "cuit": "",
                "domicilio_comercial": "",
                "condicion_iva": "",
                "condicion_venta": ""
            },
            "items": [
                {
                    "codigo": "",
                    "descripcion": "",
                    "cantidad": None,
                    "unidad_medida": "",
                    "precio_unitario": None,
                    "bonificacion": None,
                    "subtotal": None,
                    "alicuota_iva": "",
                    "iva_monto": None,
                    "subtotal_con_iva": None
                }
            ],
            "totales": {
                "importe_neto_gravado": None,
                "importe_otros_tributos": None,
                "iva_21": None,
                "iva_27": None,
                "iva_105": None,
                "iva_5": None,
                "iva_25": None,
                "iva_0": None,
                "importe_total": None
            },
            "cae": {
                "numero": "",
                "fecha_vencimiento": ""
            },
             "qr": {
                 "contenido": ""
            }
        }
    }
