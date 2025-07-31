from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    position: str
    height_cm: int
    weight_kg: int
    preferred_foot: str  # "left", "right", or "both"
    is_goalkeeper: bool

    # Hidden stats
    ambition: int
    consistency: int
    injury_proneness: int
    potential: int  # fixed between 1–200

    club_id: int = Field(foreign_key="club.id")
    club: Optional["Club"] = Relationship(back_populates="squad")

    # Use forward reference string to avoid import cycles
    stats: List["PlayerStat"] = Relationship(back_populates="player")