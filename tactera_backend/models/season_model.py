# season_models.py
# Defines SeasonState, which tracks the current season and round of each league.

from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field


# season_model.py
# Defines Season (historical season data) and SeasonState (tracks active season progress)

from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field


class Season(SQLModel, table=True):
    """
    Represents a specific season for a league.
    Each season has a fixed start and end date (28 days) and is linked to a league.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # Link this season to a league
    league_id: int = Field(foreign_key="league.id")

    # Sequential season number (e.g., Season 1, Season 2)
    season_number: int

    # Season start and end dates (always 28 days apart)
    start_date: datetime
    end_date: datetime

    # (Future-proof) fields for season summary/stats
    winner_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    runner_up_club_id: Optional[int] = Field(default=None, foreign_key="club.id")

    def __init__(self, **kwargs):
        """
        Automatically sets end_date based on start_date if not explicitly provided.
        """
        super().__init__(**kwargs)
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + timedelta(days=28)


class SeasonState(SQLModel, table=True):
    """
    Tracks the current (active) season state for a league.
    Points to a specific Season and tracks the live round progress.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # Link to the active season
    season_id: int = Field(foreign_key="season.id")

    # Current round progress
    current_round: int = 1

    # Timestamp of last round advancement
    last_round_advanced: Optional[datetime] = None

