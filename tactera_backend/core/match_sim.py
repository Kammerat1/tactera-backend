# tactera_backend/core/match_sim.py

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
from tactera_backend.core.injury_config import REINJURY_MULTIPLIER
from tactera_backend.core.config import TEST_MODE  # ✅ Ensure TEST_MODE is imported



async def simulate_match(db: AsyncSession, fixture_id: int):
    """
    Simulates a single match and integrates reinjury risk:
    - Fully injured players are excluded.
    - Rehab-phase players can play but face increased reinjury risk.
    - Fatigue and pitch quality also affect injury risk.
    - TEST_MODE prints detailed debug logs.
    """

    # 1️⃣ Fetch fixture
    result = await db.execute(select(Match).where(Match.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise ValueError(f"Fixture with ID {fixture_id} not found.")

    # 2️⃣ Fetch clubs
    home_club = await db.get(Club, fixture.home_club_id)
    away_club = await db.get(Club, fixture.away_club_id)

    # 3️⃣ Fetch players (exclude fully injured)
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

    # 4️⃣ Stadium pitch quality
    stadium_result = await db.execute(select(Stadium).where(Stadium.club_id == home_club.id))
    stadium = stadium_result.scalar_one_or_none()
    pitch_quality = stadium.pitch_quality if stadium else 50

    # 5️⃣ Placeholder goal simulation
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)
    fixture.home_goals = home_goals
    fixture.away_goals = away_goals
    fixture.is_played = True
    fixture.match_time = datetime.utcnow()

    await db.commit()
    await db.refresh(fixture)

    # 6️⃣ Injury + Reinjury Risk Logic
    injuries = []
    base_risk = 0.05  # Baseline injury risk (5%)
    all_players = home_players + away_players

    for player in all_players:
        # Placeholder fatigue and injury proneness (future systems will enhance this)
        energy = 100  
        injury_proneness = 1.0  

        # Check for existing rehab injury
        rehab_injury = await db.execute(
            select(Injury).where(Injury.player_id == player.id, Injury.days_remaining > 0)
        )
        rehab_injury = rehab_injury.scalar_one_or_none()

        # Calculate risk
        risk = calculate_injury_risk(base_risk, pitch_quality, energy, injury_proneness)

        if rehab_injury and rehab_injury.days_remaining <= rehab_injury.rehab_start:
            risk *= REINJURY_MULTIPLIER  # ✅ Config-driven multiplier
            if TEST_MODE:
                print(f"   - Applied Reinjury Multiplier: x{REINJURY_MULTIPLIER}")


        if TEST_MODE:
            print(f"[DEBUG] Injury Check: {player.first_name} {player.last_name}")
            print(f"   - Base Risk: {base_risk*100:.2f}%")
            print(f"   - Pitch Quality: {pitch_quality}")
            print(f"   - Energy: {energy}")
            print(f"   - Rehab Phase: {'Yes' if rehab_injury else 'No'}")
            print(f"   - Final Risk: {risk*100:.2f}%")

        # Roll for injury
        if random.random() < risk:
            new_injury_data = generate_injury()
            tz = timezone(timedelta(hours=2))

            # If reinjury during rehab: overwrite injury details
            if rehab_injury:
                rehab_injury.name = new_injury_data["name"]
                rehab_injury.type = new_injury_data["type"]
                rehab_injury.severity = new_injury_data["severity"]
                rehab_injury.start_date = datetime.now(tz)
                rehab_injury.days_total = new_injury_data["days_total"]
                rehab_injury.rehab_start = new_injury_data["rehab_start"]
                rehab_injury.rehab_xp_multiplier = new_injury_data["rehab_xp_multiplier"]
                rehab_injury.fit_for_matches = False
                rehab_injury.days_remaining = new_injury_data["days_total"]
                if TEST_MODE:
                    print(f"   🔁 Reinjury Event: {player.first_name} {player.last_name} aggravated an existing injury during the match!")
            else:
                # Fresh injury assignment
                new_injury = Injury(
                    player_id=player.id,
                    name=new_injury_data["name"],
                    type=new_injury_data["type"],
                    severity=new_injury_data["severity"],
                    start_date=datetime.now(tz),
                    days_total=new_injury_data["days_total"],
                    rehab_start=new_injury_data["rehab_start"],
                    rehab_xp_multiplier=new_injury_data["rehab_xp_multiplier"],
                    fit_for_matches=new_injury_data["fit_for_matches"],
                    days_remaining=new_injury_data["days_total"]
                )
                db.add(new_injury)

            # Log injury for summary
            club_result = await db.execute(select(Club).where(Club.id == player.club_id))
            player_club = club_result.scalar_one()

            print(
                f"[{datetime.now(tz)}] 🩺 Injury Logged: "
                f"{player.first_name} {player.last_name} "
                f"({player_club.name}) suffered '{new_injury_data['name']}' "
                f"({new_injury_data['severity']}, {new_injury_data['days_total']} days)"
            )

            injuries.append({
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                "reinjury": bool(rehab_injury),  # ✅ True if aggravated an existing rehab injury
                **new_injury_data
            })

    # Final commit of injury updates
    await db.commit()
    
    if TEST_MODE:
        total_injuries = len(injuries)
        reinjury_count = sum(1 for inj in injuries if inj["reinjury"])
        print(f"\n[DEBUG] Match Summary:")
        print(f"   - Total Injuries: {total_injuries}")
        print(f"   - Reinjuries (aggravated rehab injuries): {reinjury_count}")
        print(f"   - Fixture ID: {fixture.id}\n")

    return {
        "fixture_id": fixture.id,
        "home_club_id": fixture.home_club_id,
        "away_club_id": fixture.away_club_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "played_at": fixture.match_time,
        "injuries": injuries  # For debugging
    }
