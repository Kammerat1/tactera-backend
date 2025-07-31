# match_models.py
# Defines the Match model, representing a scheduled fixture between two clubs.
## Stores the match results and stats of a simulated match
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Match(SQLModel, table=True):
    """Represents a scheduled match between two clubs in a league."""
    id: Optional[int] = Field(default=None, primary_key=True)
    league_id: int = Field(foreign_key="league.id")
    home_club_id: int = Field(foreign_key="club.id")
    away_club_id: int = Field(foreign_key="club.id")
    round_number: int
    season: int
    match_time: Optional[datetime] = None
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    is_played: bool = False


class MatchResult(SQLModel, table=True):
    """Stores the results and stats of a simulated match."""
    id: Optional[int] = Field(default=None, primary_key=True)

    home_club_id: int
    away_club_id: int
    home_goals: int
    away_goals: int

    possession_home: int
    possession_away: int
    corners_home: int
    corners_away: int
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int

    created_at: datetime = Field(default_factory=datetime.utcnow)
