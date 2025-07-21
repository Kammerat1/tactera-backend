from pydantic import BaseModel, EmailStr

class ManagerRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class ManagerLogin(BaseModel):
    email: EmailStr
    password: str
