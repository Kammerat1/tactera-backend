# match_models.py
# Defines the Match model, representing a scheduled fixture between two clubs.

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Match(SQLModel, table=True):
    """Represents a scheduled match between two clubs in a league."""
    id: Optional[int] = Field(default=None, primary_key=True)

    league_id: int = Field(foreign_key="league.id")  # League the match belongs to
    home_club_id: int = Field(foreign_key="club.id")  # Home team
    away_club_id: int = Field(foreign_key="club.id")  # Away team

    round_number: int  # Round number (e.g., 1–30)
    season: int  # In-game season number

    match_time: Optional[datetime] = None  # Future scheduling support

    # Results after simulation
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    is_played: bool = False
