# app/models/historial.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.database import Base


class HistorialArchivo(Base):
    __tablename__ = "historial_archivos"

    id = Column(Integer, primary_key=True, index=True)
    nombre_pdf = Column(String, nullable=False)
    nombre_excel = Column(String, nullable=False)
    fecha_procesado = Column(DateTime, default=datetime.utcnow)
    estado = Column(String, default="completado")
