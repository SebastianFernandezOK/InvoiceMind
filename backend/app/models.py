# models.py
from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    numeroFactura = Column(String, index=True)
    fecha = Column(Date)
    CUIT = Column(String)
    razonSocial = Column(String)
    importeTotal = Column(Float)
    importeNeto = Column(Float)
    IVA = Column(Float)
