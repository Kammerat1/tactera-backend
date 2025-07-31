# season_models.py
# Defines SeasonState, which tracks the current season and round of each league.

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class SeasonState(SQLModel, table=True):
    """Tracks the current season and round state for a league."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Link to a specific league
    league_id: int = Field(foreign_key="league.id")

    # Current season and round (e.g., Season 1, Round 5)
    current_season: int = 1
    current_round: int = 1

    # Track season timings
    season_start: datetime = Field(default_factory=datetime.utcnow)
    last_round_advanced: Optional[datetime] = None
