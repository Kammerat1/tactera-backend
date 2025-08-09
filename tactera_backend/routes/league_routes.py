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
from tactera_backend.models.player_model import Player
from tactera_backend.core.injury_config import LOW_ENERGY_THRESHOLD
from tactera_backend.models.suspension_model import Suspension


router = APIRouter()

# ---------------------------------------------
# Helpers for per-player availability (fixture view)
# ---------------------------------------------
def get_active_injury(player: Player):
    """
    Returns the first active injury for the player (if any).
    'Active' means days_remaining > 0. If none, returns None.
    """
    if getattr(player, "injuries", None):
        for inj in player.injuries:
            if inj.days_remaining > 0:
                return inj
    return None

def get_active_suspension(player: Player):
    """
    Returns the first active suspension (matches_remaining > 0) for the player, if any.
    Otherwise returns None.
    """
    if getattr(player, "suspensions", None):
        for sus in player.suspensions:
            if sus.matches_remaining and sus.matches_remaining > 0:
                return sus
    return None

def compute_player_availability(player: Player) -> str:
    """
    Derives a single availability status for a player (priority order):
    1) "suspended": has an active suspension (matches_remaining > 0)
    2) "injured":   active injury with days_remaining > rehab_start
    3) "rehab":     active injury with 0 < days_remaining <= rehab_start
    4) "tired":     no injury/suspension and energy < LOW_ENERGY_THRESHOLD
    5) "ok":        otherwise
    """
    # 1) Suspension trumps everything else
    if get_active_suspension(player):
        return "suspended"

    # 2) Injury checks
    active_injury = get_active_injury(player)
    if active_injury:
        if active_injury.days_remaining <= active_injury.rehab_start:
            return "rehab"
        return "injured"

    # 3) Energy check
    if player.energy < LOW_ENERGY_THRESHOLD:
        return "tired"

    # 4) Default
    return "ok"

# ---------------------------------------------
# Availability helper for fixture list badges
# ---------------------------------------------
def compute_availability_counts(session: Session, club_id: int) -> dict:
    """
    Computes availability summary for a club's squad.
    Returns counts for: injured, rehab, tired, suspended, ok.

    Rules:
    - injured: player has an active injury (days_remaining > rehab_start)
    - rehab: player has an active injury and is in the rehab phase
             (days_remaining > 0 AND days_remaining <= rehab_start)
    - tired: player has NO active injury and energy < LOW_ENERGY_THRESHOLD
    - suspended: currently not implemented in backend -> always 0
    - ok: everyone else (no active injury and not tired)

    Notes:
    - We scan the player's injuries and pick the first with days_remaining > 0
      to treat as the active injury (same idea as in /clubs/.../squad).
    """
    counts = {"injured": 0, "rehab": 0, "tired": 0, "suspended": 0, "ok": 0}

    # Fetch all players for this club
    players = session.exec(select(Player).where(Player.club_id == club_id)).all()

    for p in players:
        # Default assumption
        status = "ok"
        
                # Suspension first
        if get_active_suspension(p):
            status = "suspended"
        else:
            # (existing injury and energy logic remains)
            ...
        # 1) Check for an active injury
        active_injury = None
        if getattr(p, "injuries", None):
            for inj in p.injuries:
                # "Active" is defined as: still has days remaining
                if inj.days_remaining > 0:
                    active_injury = inj
                    break

        if active_injury:
            # Distinguish between "injured" (pre-rehab) and "rehab" (late recovery)
            if active_injury.days_remaining <= active_injury.rehab_start:
                status = "rehab"
            else:
                status = "injured"
        else:
            # 2) No active injury → check energy for "tired"
            if p.energy < LOW_ENERGY_THRESHOLD:
                status = "tired"
            # 3) Suspensions are not implemented yet → remains "ok"

        counts[status] += 1

    return counts


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

    # Build a lightweight, frontend-friendly payload
    fixtures_payload = []
    for fx in fixtures:
        # Fetch club names for convenience (frontend can show them directly)
        home_club = session.get(Club, fx.home_club_id)
        away_club = session.get(Club, fx.away_club_id)

        # Compute availability summaries for each side
        home_avail = compute_availability_counts(session, fx.home_club_id)
        away_avail = compute_availability_counts(session, fx.away_club_id)

        fixtures_payload.append({
            "fixture_id": fx.id,
            "round_number": fx.round_number,
            "match_time": fx.match_time,
            "home_club_id": fx.home_club_id,
            "home_club_name": home_club.name if home_club else None,
            "away_club_id": fx.away_club_id,
            "away_club_name": away_club.name if away_club else None,
            "home_availability": home_avail,   # {injured, rehab, tired, suspended, ok}
            "away_availability": away_avail,   # {injured, rehab, tired, suspended, ok}
            # Consider the match "played" if both goal values exist
            "played": (fx.home_goals is not None and fx.away_goals is not None),
            "home_goals": fx.home_goals,
            "away_goals": fx.away_goals,
        })

    return {
        "league": league.name,
        "season_number": season.season_number,
        "fixtures": fixtures_payload
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
async def advance_round(league_id: int, db: AsyncSession = Depends(get_db)):
    """
    Advances the current round for the active season of a league (async version).
    """
    # 1. Fetch the active season state for this league
    result = await db.execute(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    )
    state = result.scalar_one_or_none()

    if not state:
        raise HTTPException(status_code=404, detail="No active season state found for this league.")

    # 2. Increment the round
    state.current_round += 1
    db.add(state)
    await db.commit()

    return {"message": f"✅ Round advanced to {state.current_round} for league {league_id}"}

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
    - Finds the active season and current round.
    - Simulates all unplayed fixtures for the round.
    - Advances to the next round (or completes season if final).
    """
    # 1. Fetch the active season state
    result = await db.execute(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    )
    season_state = result.scalar_one_or_none()

    if not season_state:
        raise HTTPException(status_code=404, detail="No active season state found for this league.")

    current_round = season_state.current_round

    # 2. Fetch league & clubs
    league_result = await db.execute(select(League).where(League.id == league_id))
    league = league_result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found.")

    club_result = await db.execute(select(Club).where(Club.league_id == league_id))
    clubs = club_result.scalars().all()
    num_clubs = len(clubs)
    final_round = (num_clubs - 1) * 2  # double round robin

    # 3. Fetch unplayed matches for current round
    match_result = await db.execute(
        select(Match)
        .where(
            Match.league_id == league_id,
            Match.season_id == season_state.season_id,
            Match.round_number == current_round,
            Match.is_played == False
        )
    )
    matches = match_result.scalars().all()

    if not matches:
        return {
            "message": f"No unplayed fixtures found in round {current_round} for league {league_id}.",
            "results": []
        }

    # 4. Simulate matches
    results = []
    for match in matches:
        result = await simulate_match(db, match.id)
        results.append(result)

    # 5. Advance round or complete season
    if season_state.current_round < final_round:
        season_state.current_round += 1
        db.add(season_state)
        await db.commit()
        round_message = f"✅ Simulated round {current_round}. Advanced to round {season_state.current_round}."
    else:
        season_state.is_completed = True
        db.add(season_state)
        await db.commit()
        round_message = f"✅ Simulated final round {current_round}. Season marked complete."

    return {
        "message": round_message,
        "results": results
    }

@router.get("/fixtures/{fixture_id}/availability")
def get_fixture_availability(fixture_id: int, session: Session = Depends(get_session)):
    """
    Returns per-player availability for both clubs in a specific fixture.
    Each player includes:
    - availability_status: "injured" | "rehab" | "tired" | "suspended" | "ok"
    - a minimal active_injury summary if present
    """
    # 1) Load the fixture
    fixture = session.get(Match, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # 2) Resolve clubs (nice for response)
    home_club = session.get(Club, fixture.home_club_id) if fixture.home_club_id else None
    away_club = session.get(Club, fixture.away_club_id) if fixture.away_club_id else None

    # 3) Load both squads
    home_players = session.exec(select(Player).where(Player.club_id == fixture.home_club_id)).all()
    away_players = session.exec(select(Player).where(Player.club_id == fixture.away_club_id)).all()

    def serialize_player(p: Player) -> dict:
        """
        Converts a Player row into a minimal dict for the UI with availability_status.
        Includes an active_injury summary if applicable.
        """
        status = compute_player_availability(p)
        active_injury = get_active_injury(p)

        injury_summary = None
        if active_injury:
            injury_summary = {
                "name": active_injury.name,
                "days_remaining": active_injury.days_remaining,
                "rehab_start": active_injury.rehab_start,
                "start_date": active_injury.start_date,
                "days_total": active_injury.days_total,
            }

        return {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "position": p.position,
            "energy": p.energy,
            "availability_status": status,
            "active_injury": injury_summary,
        }

    # 4) Build response
    return {
        "fixture_id": fixture.id,
        "round_number": fixture.round_number,
        "match_time": fixture.match_time,
        "played": (fixture.home_goals is not None and fixture.away_goals is not None),
        "home": {
            "club_id": fixture.home_club_id,
            "club_name": home_club.name if home_club else None,
            "squad": [serialize_player(p) for p in home_players],
        },
        "away": {
            "club_id": fixture.away_club_id,
            "club_name": away_club.name if away_club else None,
            "squad": [serialize_player(p) for p in away_players],
        },
    }
