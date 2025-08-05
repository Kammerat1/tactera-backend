import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from tactera_backend.models.match_model import Match
from tactera_backend.models.player_model import Player
from tactera_backend.models.club_model import Club
from tactera_backend.models.stadium_model import Stadium
from tactera_backend.models.injury_model import Injury
from tactera_backend.core.injury_generator import calculate_injury_risk, generate_injury

async def simulate_match(db: AsyncSession, fixture_id: int):
    """
    Simulates a single match (with injury persistence).
    - Fetches fixture, clubs, players, stadium pitch quality.
    - Generates match result and commits injuries to DB.
    """

    # 1️⃣ Fetch the fixture
    result = await db.execute(select(Match).where(Match.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise ValueError(f"Fixture with ID {fixture_id} not found.")

    # 2️⃣ Fetch clubs
    home_club = await db.get(Club, fixture.home_club_id)
    away_club = await db.get(Club, fixture.away_club_id)

    # 3️⃣ Fetch players (exclude injured players)
    home_players_result = await db.execute(
        select(Player).where(
            Player.club_id == home_club.id,
            ~Player.id.in_(select(Injury.player_id).where(Injury.days_remaining > 0))
        )
    )
    home_players = home_players_result.scalars().all()

    away_players_result = await db.execute(
        select(Player).where(
            Player.club_id == away_club.id,
            ~Player.id.in_(select(Injury.player_id).where(Injury.days_remaining > 0))
        )
    )
    away_players = away_players_result.scalars().all()

    # 4️⃣ Fetch stadium for pitch quality
    stadium_result = await db.execute(select(Stadium).where(Stadium.club_id == home_club.id))
    stadium = stadium_result.scalar_one_or_none()
    pitch_quality = stadium.pitch_quality if stadium else 50

    # 5️⃣ Basic goal simulation (placeholder)
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)

    fixture.home_goals = home_goals
    fixture.away_goals = away_goals
    fixture.is_played = True
    fixture.match_time = datetime.utcnow()

    await db.commit()
    await db.refresh(fixture)

    # 6️⃣ Injury logic (with DB storage)
    injuries = []
    base_risk = 0.05  # 5% baseline risk
    all_players = home_players + away_players

    for player in all_players:
        energy = 100  # Placeholder until energy system added
        injury_proneness = 1.0  # Placeholder until hidden stat added
        risk = calculate_injury_risk(base_risk, pitch_quality, energy, injury_proneness)

        if random.random() < risk:
            injury_data = generate_injury()
            tz = timezone(timedelta(hours=2))
            # ✅ Store injury in DB
            new_injury = Injury(
                player_id=player.id,
                name=injury_data["name"],
                type=injury_data["type"],
                severity=injury_data["severity"],
                start_date=datetime.now(tz),
                days_total=injury_data["days_total"],
                rehab_start=injury_data["rehab_start"],
                rehab_xp_multiplier=injury_data["rehab_xp_multiplier"],
                fit_for_matches=injury_data["fit_for_matches"],
                days_remaining=injury_data["days_total"]
            )
            db.add(new_injury)
            
            club_result = await db.execute(select(Club).where(Club.id == player.club_id))
            player_club = club_result.scalar_one()

            
            print(
            f"[{datetime.now(tz)}] 🩺 Injury Logged: "
            f"{player.first_name} {player.last_name} "
            f"({player_club.name}) suffered '{injury_data['name']}' "
            f"({injury_data['severity']}, {injury_data['days_total']} days)"
            )


            injuries.append({
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                **injury_data
            })

    # ✅ Commit injuries after processing all players
    await db.commit()

    return {
        "fixture_id": fixture.id,
        "home_club_id": fixture.home_club_id,
        "away_club_id": fixture.away_club_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "played_at": fixture.match_time,
        "injuries": injuries  # Debug output (injuries also saved to DB)
    }
