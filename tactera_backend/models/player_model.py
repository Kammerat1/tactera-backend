# tactera_backend/models/player_model.py
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from tactera_backend.models.club_model import Club

if TYPE_CHECKING:
    from .injury_model import Injury
    from .suspension_model import Suspension
    from .contract_model import PlayerContract  # NEW


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

    club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    club: Optional["Club"] = Relationship(back_populates="squad")

    stats: List["PlayerStat"] = Relationship(back_populates="player")

    # Injury and suspension relationships
    injuries: List["Injury"] = Relationship(back_populates="player")
    suspensions: List["Suspension"] = Relationship(back_populates="player")
    
    # NEW: Contract relationship
    current_contract: Optional["PlayerContract"] = Relationship(back_populates="player")


# -------------------------------
# Pydantic schemas for API responses
# -------------------------------
from pydantic import BaseModel
from datetime import datetime, date
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
        from_attributes = True

# NEW: Contract schema for player responses
class ContractSummary(BaseModel):
    """Minimal contract info for player responses"""
    daily_wage: int
    contract_expires: date
    days_remaining: int
    auto_generated: bool
    
    class Config:
        from_attributes = True

class PlayerRead(BaseModel):
    """Schema for returning player details with optional active injury and contract info."""
    id: int
    first_name: str
    last_name: str
    age: int
    position: str
    height_cm: int
    weight_kg: int
    preferred_foot: str
    is_goalkeeper: bool

    # Status information
    active_injury: Optional[InjuryRead] = None
    current_contract: Optional[ContractSummary] = None  # NEW

    class Config:
        from_attributes = True