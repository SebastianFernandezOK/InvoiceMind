# crud.py
from sqlalchemy.orm import Session
from . import models, schemas

def crear_factura(db: Session, factura: schemas.FacturaCreate):
    db_factura = models.Factura(**factura.dict())
    db.add(db_factura)
    db.commit()
    db.refresh(db_factura)
    return db_factura
