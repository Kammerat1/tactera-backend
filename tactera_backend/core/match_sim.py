import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from tactera_backend.models.match_model import Match
from tactera_backend.models.player_model import Player
from tactera_backend.models.club_model import Club
from tactera_backend.models.stadium_model import Stadium
from tactera_backend.core.injury_generator import calculate_injury_risk, generate_injury

# -------------------------------------------------------------
# Enhanced Match Simulator (with injury system)
# -------------------------------------------------------------

async def simulate_match(db: AsyncSession, fixture_id: int):
    """
    Simulates a single match (with injuries) and updates the DB.

    Args:
        db (AsyncSession): Active database session.
        fixture_id (int): ID of the fixture to simulate.

    Returns:
        dict: Simulated match result (fixture_id, goals, injuries, etc.)
    """

    # 1️⃣ Fetch the fixture
    result = await db.execute(select(Match).where(Match.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise ValueError(f"Fixture with ID {fixture_id} not found.")

    # 2️⃣ Fetch clubs
    home_club = await db.get(Club, fixture.home_club_id)
    away_club = await db.get(Club, fixture.away_club_id)

    # 3️⃣ Fetch players for both clubs
    home_players_result = await db.execute(select(Player).where(Player.club_id == home_club.id))
    home_players = home_players_result.scalars().all()

    away_players_result = await db.execute(select(Player).where(Player.club_id == away_club.id))
    away_players = away_players_result.scalars().all()

    # 4️⃣ Fetch stadium for pitch quality (corrected)
    stadium_result = await db.execute(select(Stadium).where(Stadium.club_id == home_club.id))
    stadium = stadium_result.scalar_one_or_none()
    pitch_quality = stadium.pitch_quality if stadium else 50  # Default to 50 if no stadium

    # 5️⃣ Basic goal simulation (placeholder)
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)

    # Update fixture result in DB
    fixture.home_goals = home_goals
    fixture.away_goals = away_goals
    fixture.is_played = True
    fixture.match_time = datetime.utcnow()

    await db.commit()
    await db.refresh(fixture)

    # 6️⃣ Injury logic
    injuries = []
    base_risk = 0.05  # 5% baseline risk

    all_players = home_players + away_players
    for player in all_players:
        energy = 100  # Placeholder (to be dynamic later)
        injury_proneness = 1.0  # Placeholder (hidden stat later)

        risk = calculate_injury_risk(base_risk, pitch_quality, energy, injury_proneness)

        if random.random() < risk:
            injury_data = generate_injury()
            injuries.append({
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                **injury_data
            })

    return {
        "fixture_id": fixture.id,
        "home_club_id": fixture.home_club_id,
        "away_club_id": fixture.away_club_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "played_at": fixture.match_time,
        "injuries": injuries  # Debug output (later DB integration)
    }
