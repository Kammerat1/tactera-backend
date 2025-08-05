from sqlmodel import SQLModel, Field, Relationship  # ✅ add Relationship here
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .player_model import Player  # ✅ forward reference to avoid circular import

class Injury(SQLModel, table=True):
    """Tracks player injuries, their recovery progress, and match availability."""
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    name: str  # Injury name (e.g., "Hamstring Strain")
    type: str  # e.g., "muscle", "joint"
    severity: str  # minor, moderate, severe, major
    start_date: datetime
    days_total: int
    rehab_start: int  # Day number when rehab begins
    rehab_xp_multiplier: float  # XP modifier during rehab
    fit_for_matches: bool = Field(default=False)  # Whether cleared for matches
    days_remaining: int  # Countdown until recovery

    # ✅ NEW: Relationship back to Player
    player: "Player" = Relationship(back_populates="injuries")
