from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .injury_model import Injury  # ✅ forward reference for Injury
    from .suspension_model import Suspension  # ✅ forward reference for Suspension


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    age: int
    energy: int = Field(default=100, ge=0, le=100, description="Current energy level (0–100)")
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

    stats: List["PlayerStat"] = Relationship(back_populates="player")

    # ✅ NEW: Relationship to injuries
    injuries: List["Injury"] = Relationship(back_populates="player")
    
    # ✅ NEW: Relationship to suspensions
    # A player can have zero or more Suspension entries.
    # If any has matches_remaining > 0, the player is currently suspended.
    suspensions: List["Suspension"] = Relationship(back_populates="player")


# -------------------------------
# Pydantic schemas for API responses
# -------------------------------
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InjuryRead(BaseModel):
    """Schema for returning injury details in player responses (UTC+2)."""
    name: str
    type: str
    severity: str
    start_date: datetime  # Already stored in UTC+2
    days_remaining: int
    rehab_start: int
    rehab_xp_multiplier: float
    fit_for_matches: bool

    class Config:
        from_attributes = True  # ✅ Pydantic v2 equivalent of orm_mode



class PlayerRead(BaseModel):
    """Schema for returning player details with optional active injury info."""
    id: int
    first_name: str
    last_name: str
    age: int
    position: str
    height_cm: int
    weight_kg: int
    preferred_foot: str
    is_goalkeeper: bool

    # ✅ Add active injury (None if healthy)
    active_injury: Optional[InjuryRead] = None  

    class Config:
        from_attributes = True  # ✅ Pydantic v2 equivalent of orm_mode

