# match.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import MatchResult
from tactera_backend.core.database import get_session
from tactera_backend.models.player_model import Player
import random

router = APIRouter()

# === MATCH SIMULATION ENDPOINT ===

@router.post("/simulate")
def simulate_match(home_email: str, away_email: str, session: Session = Depends(get_session)):
    # --- Fetch both clubs by manager email ---
    home_club = session.exec(select(Club).where(Club.manager_email == home_email)).first()
    away_club = session.exec(select(Club).where(Club.manager_email == away_email)).first()

    if not home_club or not away_club:
        raise HTTPException(status_code=404, detail="One or both clubs not found.")

    # --- Load players for each club ---
    home_players = session.exec(select(Player).where(Player.club_id == home_club.id)).all()
    away_players = session.exec(select(Player).where(Player.club_id == away_club.id)).all()

    if not home_players or not away_players:
        raise HTTPException(status_code=400, detail="One or both clubs have no players.")

    # --- Calculate average stats ---
    def average(players, stat):
        return sum(getattr(p, stat) for p in players) / len(players)

    home_stats = {
        "pace": average(home_players, "pace"),
        "passing": average(home_players, "passing"),
        "defending": average(home_players, "defending")
    }

    away_stats = {
        "pace": average(away_players, "pace"),
        "passing": average(away_players, "passing"),
        "defending": average(away_players, "defending")
    }

    # --- Match simulation logic ---
    def simulate_team(attack, defense):
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

    # --- Cosmetic stats ---
    possession_home = random.randint(45, 55)
    possession_away = 100 - possession_home
    corners_home = random.randint(2, 7)
    corners_away = random.randint(2, 7)

    # --- Save match result to database ---
    result = MatchResult(
        home_club_id=home_club.id,
        away_club_id=away_club.id,
        home_goals=goals_home,
        away_goals=goals_away,
        possession_home=possession_home,
        possession_away=possession_away,
        corners_home=corners_home,
        corners_away=corners_away,
        shots_home=shots_home,
        shots_away=shots_away,
        shots_on_target_home=on_target_home,
        shots_on_target_away=on_target_away
    )

    session.add(result)
    session.commit()
    session.refresh(result)

    # --- Return match result as response ---
    return {
        "match_id": result.id,
        "home_club": home_club.club_name,
        "away_club": away_club.club_name,
        "home_goals": result.home_goals,
        "away_goals": result.away_goals,
        "shots": {
            "home": result.shots_home,
            "away": result.shots_away
        },
        "on_target": {
            "home": result.shots_on_target_home,
            "away": result.shots_on_target_away
        },
        "possession": {
            "home": result.possession_home,
            "away": result.possession_away
        },
        "corners": {
            "home": result.corners_home,
            "away": result.corners_away
        }
    }
