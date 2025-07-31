# league.py
# This file defines the League model for Tactera.

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class League(SQLModel, table=True):
    """Database model representing a football league."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    nation: str  # Country or nation the league belongs to

    # Relationship to clubs (a league contains many clubs)
    clubs: List["Club"] = Relationship(back_populates="league")
