from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import MatchResult
from tactera_backend.core.database import get_session
from tactera_backend.models.player_model import Player
import random
from tactera_backend.models.player_stat_model import PlayerStat
from datetime import datetime, timedelta, timezone

# --- Injury imports ---
from tactera_backend.core.injury_generator import calculate_injury_risk, generate_injury
from tactera_backend.core.injury_config import REINJURY_MULTIPLIER
from tactera_backend.models.stadium_model import Stadium
from tactera_backend.models.injury_model import Injury
from tactera_backend.core.config import TEST_MODE

# ✅ Define router BEFORE using it
router = APIRouter()


@router.post("/simulate")
def simulate_match(home_email: str, away_email: str, session: Session = Depends(get_session)):
    """
    Simulates a match between two clubs.
    Now includes:
    - Injury generation with reinjury risk for rehab-phase players.
    - Pitch quality effects.
    - Stat-based simulation for shots and goals.
    """

    # 1️⃣ Fetch clubs
    home_club = session.exec(select(Club).where(Club.manager_email == home_email)).first()
    away_club = session.exec(select(Club).where(Club.manager_email == away_email)).first()
    if not home_club or not away_club:
        raise HTTPException(status_code=404, detail="One or both clubs not found.")

    # 2️⃣ Fetch home stadium for pitch quality
    stadium = session.exec(select(Stadium).where(Stadium.club_id == home_club.id)).first()
    if not stadium:
        raise HTTPException(status_code=404, detail="Home stadium not found.")
    pitch_quality = stadium.pitch_quality

    # 3️⃣ Fetch players (including rehab-phase players)
    home_players = session.exec(select(Player).where(Player.club_id == home_club.id)).all()
    away_players = session.exec(select(Player).where(Player.club_id == away_club.id)).all()
    if not home_players or not away_players:
        raise HTTPException(status_code=400, detail="One or both clubs have no players.")

    # 4️⃣ Build stat dictionaries
    expected_stats = ["pace", "passing", "defending", "stamina", "vision", "finishing"]

    def get_average_stat(stat: str, players: list) -> float:
        if not players:
            return 0
        player_ids = [p.id for p in players]
        stat_records = session.exec(
            select(PlayerStat).where(
                PlayerStat.player_id.in_(player_ids),
                PlayerStat.stat_name == stat
            )
        ).all()
        if not stat_records:
            return 0
        return sum(s.value for s in stat_records) / len(stat_records)

    home_stats = {stat: get_average_stat(stat, home_players) for stat in expected_stats}
    away_stats = {stat: get_average_stat(stat, away_players) for stat in expected_stats}

    # 5️⃣ Basic match simulation (shots & goals)
    def simulate_team(attack: float, defense: float):
        value = (attack + random.uniform(0, 10)) - (defense * 0.5)
        shots = max(1, int(value / 2))
        shots_on_target = max(1, shots - random.randint(0, 3))
        goals = random.randint(0, shots_on_target)
        return shots, shots_on_target, goals

    shots_home, on_target_home, goals_home = simulate_team(
        home_stats["passing"] + home_stats["pace"],
        away_stats["defending"]
    )
    shots_away, on_target_away, goals_away = simulate_team(
        away_stats["passing"] + away_stats["pace"],
        home_stats["defending"]
    )

    # 6️⃣ Injury & Reinjury Risk
    all_players = home_players + away_players
    base_risk = 0.05
    tz = timezone(timedelta(hours=2))
    injuries = []

    for player in all_players:
        energy = 100  # placeholder until fatigue system added
        proneness = 1.0  # placeholder until hidden trait added

        # Check for active rehab injury
        rehab_injury = session.exec(
            select(Injury).where(Injury.player_id == player.id, Injury.days_remaining > 0)
        ).first()

        risk = calculate_injury_risk(base_risk, pitch_quality, energy, proneness)
        if rehab_injury and rehab_injury.days_remaining <= rehab_injury.rehab_start:
            risk *= REINJURY_MULTIPLIER
            if TEST_MODE:
                print(f"   🔁 Reinjury Risk Applied: {player.first_name} {player.last_name} (x{REINJURY_MULTIPLIER})")

        if TEST_MODE:
            print(f"[DEBUG] Injury Roll: {player.first_name} {player.last_name} - Final Risk {risk:.2%}")

        # Roll injury
        if random.random() < risk:
            injury_data = generate_injury()

            if rehab_injury and rehab_injury.days_remaining <= rehab_injury.rehab_start:
                # 🔁 Reinjury: overwrite current injury
                rehab_injury.name = injury_data["name"]
                rehab_injury.type = injury_data["type"]
                rehab_injury.severity = injury_data["severity"]
                rehab_injury.start_date = datetime.now(tz)
                rehab_injury.days_total = injury_data["days_total"]
                rehab_injury.rehab_start = injury_data["rehab_start"]
                rehab_injury.rehab_xp_multiplier = injury_data["rehab_xp_multiplier"]
                rehab_injury.fit_for_matches = False
                rehab_injury.days_remaining = injury_data["days_total"]

                if TEST_MODE:
                    print(f"   🔁 Reinjury Event: {player.first_name} aggravated existing injury!")
                reinjury_flag = True
            else:
                # Fresh injury
                new_injury = Injury(
                    player_id=player.id,
                    name=injury_data["name"],
                    type=injury_data["type"],
                    severity=injury_data["severity"],
                    start_date=datetime.now(tz),
                    days_total=injury_data["days_total"],
                    rehab_start=injury_data["rehab_start"],
                    rehab_xp_multiplier=injury_data["rehab_xp_multiplier"],
                    fit_for_matches=False,
                    days_remaining=injury_data["days_total"]
                )
                session.add(new_injury)
                reinjury_flag = False

            injuries.append({
                "player": f"{player.first_name} {player.last_name}",
                "reinjury": reinjury_flag,
                **injury_data
            })

            if TEST_MODE:
                print(f"🩺 Injury Logged: {player.first_name} {player.last_name} - {injury_data['name']} ({injury_data['severity']})")

    session.commit()

    # ✅ Summary calculations
    if TEST_MODE:
        total = len(injuries)
        reinjuries = sum(1 for inj in injuries if inj["reinjury"])
        new_injuries = total - reinjuries
        print(f"\n[DEBUG] Match Injury Summary: Total={total}, New={new_injuries}, Reinjuries={reinjuries}\n")

    # ✅ Split injuries by team
    home_injuries = [inj for inj in injuries if any(p.id == inj["player_id"] for p in home_players)]
    away_injuries = [inj for inj in injuries if any(p.id == inj["player_id"] for p in away_players)]

    # ✅ Return data
    return {
        "home_goals": goals_home,
        "away_goals": goals_away,
        "shots": {"home": shots_home, "away": shots_away},
        "on_target": {"home": on_target_home, "away": on_target_away},
        "injuries": injuries,
        "reinjury_count": reinjuries,            # Total aggravated injuries
        "new_injury_count": new_injuries,        # Total fresh injuries
        "home_injuries": home_injuries,          # Injuries for home team only
        "away_injuries": away_injuries           # Injuries for away team only
    }



