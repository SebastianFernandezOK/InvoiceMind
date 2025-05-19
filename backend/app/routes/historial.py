# app/routes/historial.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.historial import obtener_historial

router = APIRouter(prefix="/historial", tags=["Historial"])

@router.get("/")
def listar_historial(db: Session = Depends(get_db)):
    return obtener_historial(db)
