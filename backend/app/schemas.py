# schemas.py
from pydantic import BaseModel
from datetime import date

class FacturaBase(BaseModel):
    numeroFactura: str
    fecha: date
    CUIT: str
    razonSocial: str
    importeTotal: float
    importeNeto: float
    IVA: float

class FacturaCreate(FacturaBase):
    pass

class Factura(FacturaBase):
    id: int

    class Config:
        orm_mode = True
