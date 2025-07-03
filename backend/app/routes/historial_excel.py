from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.historial_excel import obtener_historial_excel as crud_obtener_historial_excel, obtener_excel_por_id
from app.routes.auth import get_current_user, User
from io import BytesIO

router = APIRouter(prefix="/excel", tags=["Historial Excel"])

@router.get("/")
def listar_historial_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener el historial de archivos Excel del usuario"""
    return crud_obtener_historial_excel(db, current_user.id)

@router.get("/descargar/{excel_id}")
def descargar_excel(
    excel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Descargar un archivo Excel específico del historial"""
    excel_record = obtener_excel_por_id(db, excel_id, current_user.id)
    
    if not excel_record:
        raise HTTPException(status_code=404, detail="Archivo Excel no encontrado")
    
    # Crear el stream de respuesta
    excel_stream = BytesIO(excel_record.excel_data)
    
    return StreamingResponse(
        BytesIO(excel_record.excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={excel_record.nombre_archivo}"}
    )
