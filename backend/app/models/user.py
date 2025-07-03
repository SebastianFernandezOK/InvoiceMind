from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(String, default="basico", nullable=False)  # basico, profesional, empresarial
    procesamientos_restantes = Column(Integer, default=100, nullable=False)
    procesamientos_totales = Column(Integer, default=100, nullable=False)
    
    # Relaciones
    historial_archivos = relationship("HistorialArchivo", back_populates="user")
    historial_excel = relationship("HistorialExcel", back_populates="user")