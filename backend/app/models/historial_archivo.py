# app/models/historial.py
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class HistorialArchivo(Base):
    __tablename__ = "historial_archivos"

    id = Column(Integer, primary_key=True, index=True)
    nombre_pdf = Column(String, nullable=False)
    nombre_excel = Column(String, nullable=False)
    fecha_procesado = Column(DateTime, default=datetime.utcnow)
    estado = Column(String, default="completado")
    pdf_data = Column(LargeBinary, nullable=True)  # Guarda el binario del PDF
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Asociar al usuario
    
    # Relación con el usuario
    user = relationship("User", back_populates="historial_archivos")
