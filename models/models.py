from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

# Request models for Manager registration and login
class ManagerRegister(BaseModel):
    email: str
    password: str

class ManagerLogin(BaseModel):
    email: str
    password: str

# Manager model
class Manager(SQLModel, table=True):
    email: str = Field(primary_key=True)
    password_hash: str

    club: Optional["Club"] = Relationship(back_populates="manager")

# Club model
class Club(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    manager_email: Optional[str] = Field(default=None, foreign_key="manager.email", nullable=True)
    is_bot: bool = Field(default=False)

    league_id: Optional[int] = Field(default=None, foreign_key="league.id")
    league: Optional["League"] = Relationship(back_populates="clubs")

    trainingground_id: Optional[int] = Field(default=None, foreign_key="trainingground.id")
    last_training_date: Optional[date] = Field(default=None, nullable=True)

    squad: List["Player"] = Relationship(back_populates="club")
    manager: Optional[Manager] = Relationship(back_populates="club")

# League model
class League(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    level: int

    country_id: int = Field(foreign_key="country.id")
    country: Optional["Country"] = Relationship(back_populates="leagues")

    clubs: List[Club] = Relationship(back_populates="league")

# ⚽ Match model: represents a scheduled fixture between two clubs in a league
class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    league_id: int = Field(foreign_key="league.id")  # league the match belongs to
    home_club_id: int = Field(foreign_key="club.id")  # home team
    away_club_id: int = Field(foreign_key="club.id")  # away team

    round_number: int  # 1–30
    season: int  # in-game season number
    match_time: Optional[datetime] = None  # for future match scheduling

    home_goals: Optional[int] = None  # to be filled when match is simulated
    away_goals: Optional[int] = None
    is_played: bool = False  # set to True once match is simulated
    
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

# TrainingGround model
class TrainingGround(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: str
    xp_boost: int

# TrainingHistory model
class TrainingHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id")
    date: datetime = Field(default_factory=datetime.utcnow)
    drill_name: str
    total_xp: float
    stats: List["TrainingHistoryStat"] = Relationship(back_populates="history")

# TrainingHistoryStat model
class TrainingHistoryStat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    history_id: int = Field(foreign_key="traininghistory.id")
    player_id: int = Field(foreign_key="player.id")
    stat_name: str
    xp_gained: float
    new_value: int
    history: "TrainingHistory" = Relationship(back_populates="stats")

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
