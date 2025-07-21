from fastapi import APIRouter, HTTPException
from models import ManagerRegister, ManagerLogin
from utils import hash_password, verify_password

router = APIRouter()
fake_db = {}  # TEMPORARY storage (replaces database for now)

@router.post("/register")
def register(manager: ManagerRegister):
    if manager.email in fake_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(manager.password)
    fake_db[manager.email] = {
        "username": manager.username,
        "email": manager.email,
        "password": hashed_pw
    }
    return {"message": f"Manager {manager.username} registered successfully"}

@router.post("/login")
def login(manager: ManagerLogin):
    user = fake_db.get(manager.email)
    if not user or not verify_password(manager.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": f"Welcome back, {user['username']}!"}
