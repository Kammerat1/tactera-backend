# manager.py
# This file defines the Manager model (SQLModel) and related Pydantic request schemas.

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel


# Pydantic request models (used for API input)
class ManagerRegister(BaseModel):
    """Request model for registering a new manager."""
    email: str
    password: str


class ManagerLogin(BaseModel):
    """Request model for logging in an existing manager."""
    email: str
    password: str


# SQLModel table for Manager
class Manager(SQLModel, table=True):
    """Database model for managers controlling clubs."""
    email: str = Field(primary_key=True)
    password_hash: str

    # Relationship to Club (each manager may own one club)
    club: Optional["Club"] = Relationship(back_populates="manager")
