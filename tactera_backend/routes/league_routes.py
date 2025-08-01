from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.league_model import League
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import Match
from tactera_backend.models.season_model import Season, SeasonState

router = APIRouter()

# =========================================
# GET FIXTURES FOR A LEAGUE
# =========================================
@router.get("/league/{league_id}/fixtures")
def get_fixtures(league_id: int, session: Session = Depends(get_session)):
    """
    Fetch fixtures for the active season of a given league.
    Dynamically retrieves season info from Season + SeasonState.
    """

    # ✅ Fetch league
    league = session.exec(select(League).where(League.id == league_id)).first()
    if not league:
        return {"error": "League not found."}

    # ✅ Fetch active season via SeasonState (join Season for details)
    season_state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not season_state:
        return {"error": "No active season found for this league."}

    # ✅ Fetch Season details for season_number
    season = session.get(Season, season_state.season_id)

    # ✅ Fetch fixtures for this league + season
    fixtures = session.exec(
        select(Match)
        .where(Match.league_id == league_id, Match.season_id == season.id)
        .order_by(Match.round_number, Match.match_time)
    ).all()

    return {
        "league": league.name,
        "season_number": season.season_number,
        "fixtures": fixtures
    }


# =========================================
# GET LEAGUE STANDINGS
# =========================================
@router.get("/league/{league_id}/standings")
def get_standings(league_id: int, session: Session = Depends(get_session)):
    """
    Fetch league standings for the active season.
    """

    league = session.exec(select(League).where(League.id == league_id)).first()
    if not league:
        return {"error": "League not found."}

    # ✅ Fetch active season
    season_state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not season_state:
        return {"error": "No active season found for this league."}

    season = session.get(Season, season_state.season_id)

    # ✅ Fetch clubs in this league
    clubs = session.exec(select(Club).where(Club.league_id == league_id)).all()

    # ✅ Fetch matches for this season (played only)
    matches = session.exec(
        select(Match)
        .where(Match.league_id == league_id, Match.season_id == season.id, Match.is_played == True)
    ).all()

    # TODO: Build standings calculation logic here (points, wins, GD)

    return {
        "league": league.name,
        "season_number": season.season_number,
        "standings": [],  # Placeholder until standings logic is implemented
    }


# =========================================
# ADVANCE ROUND MANUALLY
# =========================================
@router.post("/league/{league_id}/advance-round")
def advance_round(league_id: int, session: Session = Depends(get_session)):
    """
    Advances the current round for the active season of a league.
    """
    # ✅ Fetch SeasonState for the active season
    state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not state:
        return {"error": "No active season state found for this league."}

    # Increment the round
    state.current_round += 1
    session.add(state)
    session.commit()

    return {
        "message": f"✅ Round advanced to {state.current_round} for league {league_id}"
    }
