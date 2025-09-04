# training_models.py
# This file defines training-related database models:
# TrainingGround, TrainingHistory, and TrainingHistoryStat.

from typing import Optional, List
from datetime import date
from sqlmodel import SQLModel, Field, Relationship


class TrainingGround(SQLModel, table=True):
    """
    Represents a club's training ground.
    Each training ground tier provides an XP boost to player training.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: int  # Training tier (1–4)
    name: str  # Training ground name
    xp_boost: int  # XP boost percentage (e.g., 25 = +25% XP)

    # Relationship to Club (one training ground can be used by many clubs)
    club: Optional["Club"] = Relationship(back_populates="training_ground")


class TrainingHistory(SQLModel, table=True):
    """Tracks each training session for a club."""
    id: Optional[int] = Field(default=None, primary_key=True)
    training_date: date = Field(default_factory=date.today)

    club_id: int = Field(foreign_key="club.id")
    club: "Club" = Relationship()
    
    drill_name: str  # ✅ Added field to store which drill was used
    total_xp: int    # ✅ Added field to store total XP from session

    # Training session logs for each player
    players: List["TrainingHistoryStat"] = Relationship(back_populates="training_history")


class TrainingHistoryStat(SQLModel, table=True):
    """Stores XP gains for a player in a specific training session."""
    id: Optional[int] = Field(default=None, primary_key=True)

    training_history_id: int = Field(foreign_key="traininghistory.id")
    training_history: "TrainingHistory" = Relationship(back_populates="players")

    player_id: int = Field(foreign_key="player.id")
    stat_name: str
    xp_gained: int
    new_value: int  # ✅ Added: final stat value after training
