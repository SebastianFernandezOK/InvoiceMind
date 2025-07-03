from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.historial import obtener_historial as crud_obtener_historial
from app.routes.auth import get_current_user, User

router = APIRouter(prefix="/historial", tags=["Historial"])

@router.get("/")
def listar_historial(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Protegido
):
    return crud_obtener_historial(db, current_user.id)