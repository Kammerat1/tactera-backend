# training_models.py
# This file defines training-related database models:
# TrainingGround, TrainingHistory, and TrainingHistoryStat.

from typing import Optional, List
from datetime import date
from sqlmodel import SQLModel, Field, Relationship


class TrainingGround(SQLModel, table=True):
    """Represents a club's training ground and its upgrade level."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    level: int

    # One-to-one relationship with Club
    club: Optional["Club"] = Relationship(back_populates="training_ground")


class TrainingHistory(SQLModel, table=True):
    """Tracks each training session for a club."""
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date

    club_id: int = Field(foreign_key="club.id")
    club: "Club" = Relationship()

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
