from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "supersecretkey"  # Usa una variable de entorno en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()
security = HTTPBearer()

class UserRegister(BaseModel):
    email: str
    password: str
    plan: str = "basico"  # basico, profesional, empresarial

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    plan: str
    procesamientos_restantes: int
    procesamientos_totales: int

    class Config:
        from_attributes = True

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no existe")
    return user

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Definir límites por plan
    plan_limits = {
        "basico": 100,
        "profesional": 500,
        "empresarial": 1000
    }
    
    if user.plan not in plan_limits:
        raise HTTPException(status_code=400, detail="Plan inválido")
    
    procesamientos_totales = plan_limits[user.plan]
    hashed_password = pwd_context.hash(user.password)
    
    db_user = User(
        email=user.email, 
        hashed_password=hashed_password,
        plan=user.plan,
        procesamientos_restantes=procesamientos_totales,
        procesamientos_totales=procesamientos_totales
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "Usuario registrado correctamente"}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    access_token = create_access_token(data={"sub": db_user.email})
    
    # Incluir información del usuario en la respuesta
    user_info = UserResponse.from_orm(db_user)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user_info
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)