from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.club_model import Club
from tactera_backend.models.league_model import League
from tactera_backend.models.match_model import Match
from tactera_backend.models.season_model import SeasonState
from datetime import datetime

router = APIRouter()

# ============================================
# GET FIXTURES
# ============================================
@router.get("/league/{league_id}/fixtures")
def get_fixtures(league_id: int, session: Session = Depends(get_session)):
    """
    Returns all fixtures for a league, grouped by round.
    Dynamically fetches season info from SeasonState.
    """
    league = session.exec(select(League).where(League.id == league_id)).first()
    if not league:
        return {"error": "League not found"}

    # 🔍 Fetch current season info
    season_state = session.exec(select(SeasonState).where(SeasonState.league_id == league_id)).first()
    season_number = season_state.season_number if season_state else 1  # Default to 1 if missing

    matches = session.exec(
        select(Match)
        .where(Match.league_id == league_id)
        .order_by(Match.round_number)
    ).all()

    club_ids = list({m.home_club_id for m in matches} | {m.away_club_id for m in matches})
    clubs = session.exec(select(Club).where(Club.id.in_(club_ids))).all()
    club_map = {club.id: club.club_name for club in clubs}

    result = [
        {
            "round": m.round_number,
            "home": club_map.get(m.home_club_id, "Unknown"),
            "away": club_map.get(m.away_club_id, "Unknown"),
            "played": m.is_played,
            "score": f"{m.home_goals}-{m.away_goals}" if m.is_played else "Not played"
        }
        for m in matches
    ]

    return {
        "league": league.name,
        "season": season_number,  # ✅ No more hardcoded value
        "fixtures": result
    }

# ============================================
# GET STANDINGS
# ============================================
@router.get("/league/{league_id}/standings")
def get_standings(league_id: int, session: Session = Depends(get_session)):
    """
    Returns the league standings dynamically (points, GD, etc.).
    """
    league = session.exec(select(League).where(League.id == league_id)).first()
    if not league:
        return {"error": "League not found"}

    # 🔍 Fetch current season info
    season_state = session.exec(select(SeasonState).where(SeasonState.league_id == league_id)).first()
    season_number = season_state.season_number if season_state else 1

    clubs = session.exec(select(Club).where(Club.league_id == league_id)).all()
    club_map = {club.id: club.club_name for club in clubs}

    table = {club.id: {
        "club": club_map[club.id],
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "points": 0
    } for club in clubs}

    matches = session.exec(
        select(Match).where(Match.league_id == league_id, Match.is_played == True)
    ).all()

    for m in matches:
        home = table[m.home_club_id]
        away = table[m.away_club_id]

        home["played"] += 1
        away["played"] += 1
        home["gf"] += m.home_goals
        home["ga"] += m.away_goals
        home["gd"] = home["gf"] - home["ga"]
        away["gf"] += m.away_goals
        away["ga"] += m.home_goals
        away["gd"] = away["gf"] - away["ga"]

        if m.home_goals > m.away_goals:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
        elif m.home_goals < m.away_goals:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3
        else:
            home["drawn"] += 1
            away["drawn"] += 1
            home["points"] += 1
            away["points"] += 1

    sorted_table = sorted(table.values(), key=lambda x: (-x["points"], -x["gd"], -x["gf"]))

    return {
        "league": league.name,
        "season": season_number,  # ✅ No more hardcoded value
        "standings": sorted_table
    }

# ============================================
# ADVANCE ROUND
# ============================================
@router.post("/league/{league_id}/advance-round")
def advance_round(league_id: int, session: Session = Depends(get_session)):
    """
    Advances the league to the next round.
    Validates round boundaries.
    """
    state = session.exec(select(SeasonState).where(SeasonState.league_id == league_id)).first()
    if not state:
        return {"error": "No SeasonState found for this league."}

    # TODO: Make max rounds dynamic (based on league setup)
    max_rounds = 30  # ✅ Temporary static limit (e.g., 16 clubs => 30 rounds)
    if state.current_round >= max_rounds:
        return {"error": f"Cannot advance: already at final round ({max_rounds})."}

    state.current_round += 1
    state.last_round_advanced = datetime.utcnow()

    session.add(state)
    session.commit()

    return {
        "message": f"✅ Round advanced to {state.current_round} for league {league_id}",
        "new_round": state.current_round
    }
