from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.league_model import League
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import Match
from tactera_backend.models.season_model import Season, SeasonState
from tactera_backend.services.generate_fixtures import generate_fixtures_for_league
from tactera_backend.core.database import get_db
from tactera_backend.core.match_sim import simulate_match
from sqlalchemy.ext.asyncio import AsyncSession


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
@router.get("/standings/{league_id}")
def get_standings(league_id: int, session: Session = Depends(get_session)):
    """
    Calculate and return current standings for a league's active season.
    """
    # 1. Find the active season state for this league
    season_state = session.exec(
        select(SeasonState)
        .where(SeasonState.season_id.in_(
            select(Season.id).where(Season.league_id == league_id)
        ))
    ).first()

    if not season_state:
        raise HTTPException(status_code=404, detail="Active season not found for this league.")

    active_season_id = season_state.season_id

    # 2. Fetch all clubs in this league
    clubs = session.exec(select(Club).where(Club.league_id == league_id)).all()

    standings = {club.id: {
        "club_id": club.id,
        "club_name": club.name,
        "points": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_diff": 0
    } for club in clubs}

    # 3. Fetch all played matches in this season
    matches = session.exec(
        select(Match).where(
            Match.league_id == league_id,
            Match.season_id == active_season_id,
            Match.is_played == True
        )
    ).all()

    # 4. Calculate standings
    for match in matches:
        home = standings[match.home_club_id]
        away = standings[match.away_club_id]

        home["goals_for"] += match.home_goals
        home["goals_against"] += match.away_goals
        away["goals_for"] += match.away_goals
        away["goals_against"] += match.home_goals

        if match.home_goals > match.away_goals:
            home["wins"] += 1
            home["points"] += 3
            away["losses"] += 1
        elif match.home_goals < match.away_goals:
            away["wins"] += 1
            away["points"] += 3
            home["losses"] += 1
        else:
            home["draws"] += 1
            away["draws"] += 1
            home["points"] += 1
            away["points"] += 1

    # 5. Compute GD and sort
    for club_stats in standings.values():
        club_stats["goal_diff"] = club_stats["goals_for"] - club_stats["goals_against"]

    sorted_standings = sorted(
        standings.values(),
        key=lambda x: (x["points"], x["goal_diff"], x["goals_for"]),
        reverse=True
    )

    return sorted_standings


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

@router.post("/simulate-match/{fixture_id}")
async def simulate_match_endpoint(fixture_id: int, db: Session = Depends(get_db)):
    """
    Simulates a single match by fixture ID.
    - Calls the basic match simulator.
    - Returns the result (goals + fixture info).
    """
    result = await simulate_match(db, fixture_id)
    return {
        "message": "Match simulated successfully",
        "result": result
    }

@router.post("/{league_id}/simulate-round")
async def simulate_round_endpoint(league_id: int, db: AsyncSession = Depends(get_db)):
    """
    Simulate all matches in the current round for a given league.
    - Finds the league's active season and current round.
    - Fetches all unplayed fixtures in that round.
    - Simulates each match using the existing simulate_match function.
    - Returns a summary of results.
    """
    # 1. Fetch the active season state for this league
    result = await db.execute(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    )
    season_state = result.scalar_one_or_none()

    if not season_state:
        raise HTTPException(status_code=404, detail="No active season state found for this league.")

    current_round = season_state.current_round

    # 2. Fetch all unplayed matches in this round
    result = await db.execute(
        select(Match)
        .where(
            Match.league_id == league_id,
            Match.season_id == season_state.season_id,
            Match.round_number == current_round,
            Match.is_played == False
        )
    )
    matches = result.scalars().all()

    if not matches:
        return {"message": f"No unplayed fixtures found in round {current_round} for league {league_id}."}

    # 3. Simulate each match
    results = []
    for match in matches:
        result = await simulate_match(db, match.id)
        results.append(result)

    return {
        "message": f"✅ Simulated {len(results)} matches for round {current_round} in league {league_id}.",
        "results": results
    }

