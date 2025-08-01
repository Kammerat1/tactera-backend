from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.league_model import League
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import Match
from tactera_backend.models.season_model import Season, SeasonState
from tactera_backend.services.generate_fixtures import generate_fixtures_for_league

router = APIRouter()

# =========================================
# GET FIXTURES FOR A LEAGUE
# =========================================
@router.get("/{league_id}/fixtures")
def get_fixtures(league_id: int, session: Session = Depends(get_session)):
    """
    Fetch all fixtures for the active season of a league.
    Fixtures include match date/time, home/away clubs, and round.
    """

    # Fetch league
    league = session.get(League, league_id)
    if not league:
        return {"error": "League not found."}

    # Fetch active season via SeasonState
    season_state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not season_state:
        return {"error": "No active season found for this league."}

    season = session.get(Season, season_state.season_id)

    # Fetch fixtures for this league and season
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
@router.get("/{league_id}/standings")
def get_standings(league_id: int, session: Session = Depends(get_session)):
    """
    Fetch league standings for the active season.
    """
    league = session.get(League, league_id)
    if not league:
        return {"error": "League not found."}

    season_state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not season_state:
        return {"error": "No active season found for this league."}

    season = session.get(Season, season_state.season_id)

    # Fetch clubs in this league
    clubs = session.exec(select(Club).where(Club.league_id == league_id)).all()

    # Fetch matches that have been played
    matches = session.exec(
        select(Match)
        .where(
            Match.league_id == league_id,
            Match.season_id == season.id,
            Match.is_played == True
        )
    ).all()

    # TODO: Add standings calculation (points, GD, etc.)
    return {
        "league": league.name,
        "season_number": season.season_number,
        "standings": [],  # Placeholder until calculation is implemented
    }

# =========================================
# ADVANCE ROUND MANUALLY
# =========================================
@router.post("/{league_id}/advance-round")
def advance_round(league_id: int, session: Session = Depends(get_session)):
    """
    Advances the current round for the active season of a league.
    """
    state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not state:
        return {"error": "No active season state found for this league."}

    state.current_round += 1
    session.add(state)
    session.commit()

    return {"message": f"✅ Round advanced to {state.current_round} for league {league_id}"}

# =========================================
# GENERATE FIXTURES MANUALLY
# =========================================
@router.post("/{league_id}/generate-fixtures")
def generate_fixtures_endpoint(league_id: int, session: Session = Depends(get_session)):
    """
    Manually generate fixtures for the active season of a league.
    Clears any existing fixtures and recreates them.
    """
    try:
        generate_fixtures_for_league(session, league_id)
        return {"message": f"✅ Fixtures generated successfully for league {league_id}."}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
