from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import get_session
from models import League, Match, Club

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
