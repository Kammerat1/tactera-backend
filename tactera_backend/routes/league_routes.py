from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.club_model import Club
from tactera_backend.models.league_model import League
from tactera_backend.models.match_model import Match

router = APIRouter()

@router.get("/league/{league_id}/fixtures")
def get_fixtures(league_id: int, session: Session = Depends(get_session)):
    # Get league
    league = session.exec(select(League).where(League.id == league_id)).first()
    if not league:
        return {"error": "League not found"}

    # Get all matches in the league, sorted by round number
    matches = session.exec(
        select(Match)
        .where(Match.league_id == league_id)
        .order_by(Match.round_number)
    ).all()

    # Load club names for home and away teams
    club_ids = list({m.home_club_id for m in matches} | {m.away_club_id for m in matches})
    clubs = session.exec(select(Club).where(Club.id.in_(club_ids))).all()
    club_map = {club.id: club.club_name for club in clubs}

    result = []
    for m in matches:
        result.append({
            "round": m.round_number,
            "home": club_map.get(m.home_club_id, "Unknown"),
            "away": club_map.get(m.away_club_id, "Unknown"),
            "played": m.is_played,
            "score": f"{m.home_goals}-{m.away_goals}" if m.is_played else "Not played"
        })

    return {
        "league": league.name,
        "season": 1,
        "fixtures": result
    }

@router.get("/league/{league_id}/standings")
def get_standings(league_id: int, session: Session = Depends(get_session)):
    # Get league
    league = session.exec(select(League).where(League.id == league_id)).first()
    if not league:
        return {"error": "League not found"}

    # Get clubs in league
    clubs = session.exec(select(Club).where(Club.league_id == league_id)).all()
    club_map = {club.id: club.club_name for club in clubs}

    # Initialize stats
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

    # Get all played matches
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

    # Sort standings
    sorted_table = sorted(table.values(), key=lambda x: (-x["points"], -x["gd"], -x["gf"]))

    return {
        "league": league.name,
        "season": 1,
        "standings": sorted_table
    }

from datetime import datetime
from tactera_backend.models.season_model import SeasonState

@router.post("/league/{league_id}/advance-round")
def advance_round(league_id: int, session: Session = Depends(get_session)):
    # 🔍 Find the current SeasonState
    state = session.exec(
        select(SeasonState).where(SeasonState.league_id == league_id)
    ).first()

    if not state:
        return {"error": "No SeasonState found for this league."}

    # ⏭️ Advance the round
    state.current_round += 1
    state.last_round_advanced = datetime.utcnow()

    session.add(state)
    session.commit()

    return {
        "message": f"✅ Round advanced to {state.current_round} for league {league_id}",
        "new_round": state.current_round
    }
