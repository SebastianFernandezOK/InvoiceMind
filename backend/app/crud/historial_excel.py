# app/crud/historial_excel.py

from sqlalchemy.orm import Session
from app.models.historial_excel import HistorialExcel

def crear_historial_excel(db: Session, nombre_archivo: str, user_id: int, cantidad_facturas: int, excel_data: bytes):
    registro = HistorialExcel(
        nombre_archivo=nombre_archivo,
        cantidad_facturas=cantidad_facturas,
        excel_data=excel_data,
        user_id=user_id
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

def obtener_historial_excel(db: Session, user_id: int):
    archivos = db.query(HistorialExcel).filter(
        HistorialExcel.user_id == user_id
    ).order_by(HistorialExcel.fecha_generado.desc()).all()
    return [
        {
            "id": a.id,
            "nombre_archivo": a.nombre_archivo,
            "fecha_generado": a.fecha_generado.isoformat() if a.fecha_generado else None,
            "cantidad_facturas": a.cantidad_facturas
            # NO incluir "excel_data" para no enviar datos binarios en la lista
        }
        for a in archivos
    ]

def obtener_excel_por_id(db: Session, excel_id: int, user_id: int):
    return db.query(HistorialExcel).filter(
        HistorialExcel.id == excel_id,
        HistorialExcel.user_id == user_id
    ).first()
