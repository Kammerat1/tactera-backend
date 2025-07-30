from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from passlib.context import CryptContext

from tactera_backend.core.database import get_session
from tactera_backend.models.models import Manager, ManagerRegister, ManagerLogin

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === REGISTER ===

@router.post("/register")
def register_manager(data: ManagerRegister, session: Session = Depends(get_session)):
    existing = session.exec(select(Manager).where(Manager.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Manager already exists")

    hashed = pwd_context.hash(data.password)
    new_manager = Manager(email=data.email, password_hash=hashed)
    session.add(new_manager)
    session.commit()

    return {"message": "Manager registered"}


# === LOGIN ===

@router.post("/login")
def login_manager(data: ManagerLogin, session: Session = Depends(get_session)):
    manager = session.exec(select(Manager).where(Manager.email == data.email)).first()
    if not manager:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(data.password, manager.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}
