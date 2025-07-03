# app/crud/historial.py

from sqlalchemy.orm import Session
from app.models.historial_archivo import HistorialArchivo

def crear_historial(db: Session, nombre_pdf: str, user_id: int, nombre_excel: str = None, pdf_data: bytes = None):
    registro = HistorialArchivo(
        nombre_pdf=nombre_pdf,
        nombre_excel=nombre_excel,
        pdf_data=pdf_data,
        user_id=user_id
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

def obtener_historial(db: Session, user_id: int):
    archivos = db.query(HistorialArchivo).filter(
        HistorialArchivo.user_id == user_id
    ).order_by(HistorialArchivo.fecha_procesado.desc()).all()
    return [
        {
            "id": a.id,
            "nombre_pdf": a.nombre_pdf,
            "nombre_excel": a.nombre_excel,
            "fecha_procesado": a.fecha_procesado.isoformat() if a.fecha_procesado else None,
            "estado": a.estado
            # NO incluir "pdf_data"
        }
        for a in archivos
    ]