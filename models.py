from sqlmodel import SQLModel, Field, Relationship, select
from typing import Optional, List, Literal
from pydantic import BaseModel
from datetime import datetime, date



# === REQUEST MODELS ===

class ManagerRegister(BaseModel):
    email: str
    password: str

class ManagerLogin(BaseModel):
    email: str
    password: str

# === MANAGER MODEL ===

class Manager(SQLModel, table=True):
    email: str = Field(primary_key=True)
    password_hash: str

    # One-to-one: Manager owns one club
    club: Optional["Club"] = Relationship(back_populates="manager")


# === CLUB MODEL ===

class Club(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    manager_email: str = Field(foreign_key="manager.email")

    # ✅ New: Optional link to a league
    league_id: Optional[int] = Field(default=None, foreign_key="league.id")
    league: Optional["League"] = Relationship(back_populates="clubs")

    # Link to the training ground this club owns
    trainingground_id: Optional[int] = Field(default=None, foreign_key="trainingground.id")
    last_training_date: Optional[date] = Field(default=None, nullable=True)     

    # One-to-many: Club has many players
    squad: List["Player"] = Relationship(back_populates="club")

    # Backref to Manager
    manager: Optional[Manager] = Relationship(back_populates="club")

# === PLAYER MODEL ===

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    position: str  # Could be Literal[...] later
    height_cm: int
    weight_kg: int
    preferred_foot: str  # "left", "right", or "both"
    is_goalkeeper: bool
    
    # ⚠️ Relationship temporarily defined without auto-mapping.
    # PlayerStat lives in player_stat.py, and defining it here directly caused SQLAlchemy to fail
    # due to cross-file class resolution timing. The back_populates binding will be applied
    # manually in player_stat.py after PlayerStat is defined.
    stats: List["PlayerStat"] = Relationship(sa_relationship=False)


    # HIDDEN STATS
    ambition: int
    consistency: int
    injury_proneness: int
    potential: int  # fixed between 1–200

    club_id: int = Field(foreign_key="club.id")
    club: Optional["Club"] = Relationship(back_populates="squad")


# === MATCH RESULT MODEL ===

from datetime import datetime

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

# === TRAINING GROUND MODEL ===

from datetime import datetime

class TrainingGround(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: str   # e.g. "Basic", "Elite"
    xp_boost: int  # XP awarded per training session

    # Optional: Link back to club later if needed
    # club: Optional[Club] = Relationship(back_populates="training_ground")

from sqlmodel import SQLModel, Field

class StatLevelRequirement(SQLModel, table=True):
    level: int = Field(primary_key=True)
    xp_required: int

from sqlmodel import Session
from database import engine

        # 👇 NEW: Table to store each training session
# 🆕 TrainingHistory: Records each club training event
class TrainingHistory(SQLModel, table=True):
    """
    Logs a single training event for a club.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id")              # Which club trained
    date: datetime = Field(default_factory=datetime.utcnow)  # When training occurred
    drill_name: str                                        # Drill used during training
    total_xp: float                                        # Total XP given across all players

    # One-to-many relationship to detailed stat updates
    stats: List["TrainingHistoryStat"] = Relationship(back_populates="history")


# 🆕 TrainingHistoryStat: Detailed per-player stat gains
class TrainingHistoryStat(SQLModel, table=True):
    """
    Tracks XP gains for individual players and stats during a training event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    history_id: int = Field(foreign_key="traininghistory.id")  # Link to the training history event
    player_id: int = Field(foreign_key="player.id")            # Player who trained
    stat_name: str                                             # Stat name (e.g., "passing")
    xp_gained: float                                           # XP gained for this stat
    new_value: int                                             # New stat value after XP applied

    # Backref to parent history record
    history: "TrainingHistory" = Relationship(back_populates="stats")

# 🌍 Country model: represents a nation that hosts leagues
class Country(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # e.g. "Denmark"

    # List of leagues in this country
    leagues: List["League"] = Relationship(back_populates="country")


# 🏆 League model: tied to a country and will contain clubs
class League(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # e.g. "Division 1"
    level: int  # e.g. 1 for top league, 2 for second tier

    country_id: int = Field(foreign_key="country.id")
    country: Optional[Country] = Relationship(back_populates="leagues")
        # ✅ New: One league has many clubs
    clubs: List["Club"] = Relationship(back_populates="league")


from datetime import datetime

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

from datetime import datetime

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




#TEMPORARY FUNCTION FOR READING EXCEL FILES
from sqlmodel import delete
from sqlalchemy.exc import SQLAlchemyError

def reset_statlevel_table(session: Session):
    """
    Completely clears the statlevelrequirement table.
    Only use this before re-seeding.
    """
    try:
        session.exec(delete(StatLevelRequirement))
        session.commit()
        print("✅ statlevelrequirement table cleared.")
    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Failed to clear table:", e)

# Stadium represents a football stadium linked to a club
class Stadium(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sponsor_name: Optional[str] = None
    club_id: int = Field(foreign_key="club.id")

# StadiumPart represents individual parts of a stadium that can be upgraded and degrade over time
class StadiumPart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadium.id")
    type: str  # e.g., 'stand_home', 'stand_away', 'stand_north', 'stand_south', 'pitch'
    level: int
    durability: int