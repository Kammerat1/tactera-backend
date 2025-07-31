from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
    
    # 🗓️ Tracks the current round and season for a given league
class SeasonState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Link to a specific league
    league_id: int = Field(foreign_key="league.id")

    # Current season and round (e.g. Season 1, Round 5)
    current_season: int = 1
    current_round: int = 1

    # Track when the season started and when the last round was advanced
    season_start: datetime = Field(default_factory=datetime.utcnow)
    last_round_advanced: Optional[datetime] = None

# Country model
class Country(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    leagues: List[League] = Relationship(back_populates="country")

# MatchResult model
class MatchResult(SQLModel, table=True):
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

# Stadium model
class Stadium(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sponsor_name: Optional[str] = None
    club_id: int = Field(foreign_key="club.id")

# StadiumPart model
class StadiumPart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadium.id")
    type: str
    level: int
    durability: int
