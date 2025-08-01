# tactera_backend/core/match_simulator.py

import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from tactera_backend.models.match_model import Match

# -------------------------------------------------------------
# Basic Match Simulator (MVP)
# -------------------------------------------------------------
# This function simulates a single match by:
# 1. Generating random goals for home and away teams.
# 2. Marking the match as played and saving results in the DB.
# Future expansion: weighted team strength, event logs, stats.
# -------------------------------------------------------------

async def simulate_match(db: AsyncSession, fixture_id: int):
    """
    Simulates a single match and updates the fixture in the DB.

    Args:
        db (AsyncSession): Active database session.
        fixture_id (int): ID of the fixture (Match) to simulate.

    Returns:
        dict: Simulated match result (fixture_id, home_goals, away_goals).
    """
    # Fetch the fixture by ID
    result = await db.execute(select(Match).where(Match.id == fixture_id))
    fixture = result.scalar_one_or_none()

    if not fixture:
        raise ValueError(f"Fixture with ID {fixture_id} not found.")

    # Generate random goals for now (0–4 range for realism)
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)

    # Update fixture result
    fixture.home_goals = home_goals
    fixture.away_goals = away_goals
    fixture.is_played = True
    fixture.match_time = datetime.utcnow()  # Timestamp when match is simulated

    # Commit changes to DB
    await db.commit()
    await db.refresh(fixture)

    # Return result as dict (useful for API response)
    return {
        "fixture_id": fixture.id,
        "home_club_id": fixture.home_club_id,
        "away_club_id": fixture.away_club_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "played_at": fixture.match_time
    }
