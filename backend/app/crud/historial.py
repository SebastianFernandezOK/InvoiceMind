# app/crud/historial.py

from sqlalchemy.orm import Session
from app.models.historial_archivo import HistorialArchivo

def crear_historial(db: Session, nombre_pdf: str, nombre_excel: str = None):
    registro = HistorialArchivo(
        nombre_pdf=nombre_pdf,
        nombre_excel=nombre_excel,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

def obtener_historial(db: Session, skip: int = 0, limit: int = 100):
    return db.query(HistorialArchivo).order_by(HistorialArchivo.fecha_procesado.desc()).offset(skip).limit(limit).all()
