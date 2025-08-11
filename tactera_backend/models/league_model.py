# league.py
# This file defines the League model for Tactera.

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from tactera_backend.models.country_model import Country
from tactera_backend.models.club_model import Club

class League(SQLModel, table=True):
    """Database model representing a football league."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    level: int  # e.g. 1 for top league, 2 for second tier
    group: Optional[str] = Field(default=None)
    country_id: int = Field(foreign_key="country.id")
    
    # NEW: League activation control for beta/future expansion
    is_active: bool = Field(default=True, description="Whether this league is active in the game")
    
    country: Optional[Country] = Relationship(back_populates="leagues")
    # Relationship to clubs (a league contains many clubs)
    clubs: List["Club"] = Relationship(back_populates="league")