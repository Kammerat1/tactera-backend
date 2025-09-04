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


from sqlmodel import Field

class SeasonState(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    season_id: int = Field(foreign_key="season.id")
    current_round: int = Field(default=1)
    is_completed: bool = Field(default=False)  # ✅ NEW FLAG