from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class HistorialExcel(Base):
    __tablename__ = "historial_excel"

    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String, nullable=False)
    fecha_generado = Column(DateTime, default=datetime.utcnow)
    cantidad_facturas = Column(Integer, default=0)
    excel_data = Column(LargeBinary, nullable=False)  # Archivo Excel binario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relación con el usuario
    user = relationship("User", back_populates="historial_excel")
