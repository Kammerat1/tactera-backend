from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Suspension(SQLModel, table=True):
    """Database model for temporary player suspensions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", index=True)

    # Simple reason marker (e.g., "red_card", "yellow_accumulation")
    reason: str = Field(default="unspecified")

    # Countdown of matches for which the player is unavailable
    matches_remaining: int = Field(default=1, ge=0)
    
    # NEW: Track total matches for historical data
    total_matches_suspended: int = Field(default=1, ge=1)

    # Optional metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship back to Player
    player: Optional["Player"] = Relationship(back_populates="suspensions")