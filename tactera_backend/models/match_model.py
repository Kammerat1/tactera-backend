# match_model.py
# Defines the Match model (fixtures and results) and MatchResult model (simulated stats)

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Match(SQLModel, table=True):
    """
    Represents a scheduled match (fixture) between two clubs in a league.
    Linked to a specific season and round.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    league_id: int = Field(foreign_key="league.id")        # League the match belongs to
    season_id: int = Field(foreign_key="season.id")        # Season this match is part of
    home_club_id: int = Field(foreign_key="club.id")       # Home club
    away_club_id: int = Field(foreign_key="club.id")       # Away club

    # Match details
    round_number: int                                      # Round number within the season
    match_time: Optional[datetime] = None                  # Scheduled date/time

    # Results (populated after simulation)
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    is_played: bool = False                                # Flag if match has been simulated


class MatchResult(SQLModel, table=True):
    """
    Stores the detailed results and stats of a simulated match.
    This is separated from Match to keep the core fixture table lightweight.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # Linked clubs
    home_club_id: int
    away_club_id: int

    # Goals
    home_goals: int
    away_goals: int

    # Basic match stats
    possession_home: int
    possession_away: int
    corners_home: int
    corners_away: int
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int

    created_at: datetime = Field(default_factory=datetime.utcnow)
