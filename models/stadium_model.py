# stadium_models.py
# Defines Stadium and StadiumPart models for club stadiums and their facilities.

from typing import Optional
from sqlmodel import SQLModel, Field


class Stadium(SQLModel, table=True):
    """Represents a football club's stadium."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sponsor_name: Optional[str] = None

    # Link stadium to its club
    club_id: int = Field(foreign_key="club.id")


class StadiumPart(SQLModel, table=True):
    """Represents a section or part of a stadium (e.g., stands, facilities)."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Link to the stadium it belongs to
    stadium_id: int = Field(foreign_key="stadium.id")

    type: str  # e.g., "stand", "vip_box", "parking"
    level: int  # upgrade level of this part
    durability: int  # wear level (affects maintenance/repairs)
