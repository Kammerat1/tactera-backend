from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tactera_backend.core.database import get_db
from tactera_backend.models.player_model import Player
from tactera_backend.models.formation_model import MatchSquad, MatchSubstitution, SubstitutionRequest
from tactera_backend.routes.substitution_routes import validate_substitution_request
from tactera_backend.core.database import get_session, sync_engine
from tactera_backend.models.formation_model import MatchSquad, MatchSubstitution, SubstitutionRequest
from tactera_backend.routes.substitution_routes import validate_substitution_request
from tactera_backend.models.contract_model import PlayerContract

router = APIRouter()

@router.get("/debug/players")
async def debug_list_players(db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint: List all players with their first/last name and club ID.
    """
    result = await db.execute(select(Player))
    players = result.scalars().all()
    return [
        {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "club_id": p.club_id
        }
        for p in players
    ]

from typing import Literal, Optional
from fastapi import Body, HTTPException
from sqlmodel import select
from tactera_backend.models.club_model import Club
from tactera_backend.core.training_intensity import ALLOWED_INTENSITIES

@router.get("/debug/club/{club_id}/training-intensity")
async def get_club_training_intensity(club_id: int, db: AsyncSession = Depends(get_db)):
    """Return the club's current training intensity setting."""
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return {"club_id": club_id, "training_intensity": club.training_intensity}

@router.post("/debug/club/{club_id}/training-intensity")
async def set_club_training_intensity(
    club_id: int,
    intensity: Literal["light", "normal", "hard"] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the club's training intensity.
    Hybrid rule (future): 'hard' requires physio dept >= 1.
    For now, we allow all three and will enforce when physio exists.
    """
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    intensity = intensity.lower()
    if intensity not in ALLOWED_INTENSITIES:
        raise HTTPException(status_code=400, detail=f"Invalid intensity. Allowed: {sorted(ALLOWED_INTENSITIES)}")

    # TODO (future): enforce 'hard' lock behind physio department >= 1
    club.training_intensity = intensity
    db.add(club)
    await db.commit()
    await db.refresh(club)

    return {
        "club_id": club_id,
        "training_intensity": club.training_intensity,
        "note": "Hard will be locked behind physio later.",
    }

# ==============================================
# 🧪 DEBUG: Force reinjury test states (temporary)
# Creates three controlled player states so the match simulator
# shows reinjury multipliers in one run:
# 1) One player in active rehab (days_remaining > 0 and <= rehab_start)
# 2) One player recently healed (healed within window)
# 3) One player with very low energy (e.g., 10)
# ----------------------------------------------
# IMPORTANT: Remove this route after testing.
# ==============================================
from datetime import datetime, timedelta
from fastapi import Body
from sqlmodel import select
from tactera_backend.core.database import get_session
from tactera_backend.models.player_model import Player
from tactera_backend.models.injury_model import Injury
from tactera_backend.core.injury_config import RECENT_HEALED_WINDOW_DAYS

@router.post("/debug/force-reinjury-test")
def debug_force_reinjury_test(
    club_id: int = Body(..., embed=True),
    session = Depends(get_session),
):
    """
    Tell me to...
    Force three players into known states so the reinjury multipliers can be seen:
    - Player A: Active rehab
    - Player B: Recently healed
    - Player C: Low energy
    """
    # --- fetch 3 players from this club ---
    players = session.exec(
        select(Player).where(Player.club_id == club_id).order_by(Player.id)
    ).all()

    if len(players) < 3:
        return {"ok": False, "error": "Club needs at least 3 players for this test."}

    p_rehab = players[0]
    p_recent = players[1]
    p_low = players[2]

    # --- clear existing active injuries for clarity (optional but tidy) ---
    active_injs = session.exec(
        select(Injury).where(Injury.player_id.in_([p_rehab.id, p_recent.id]))
    ).all()
    for inj in active_injs:
        # If any injury is still active, mark as fully healed to avoid confusion
        if inj.days_remaining and inj.days_remaining > 0:
            inj.days_remaining = 0
            inj.fit_for_matches = True
    session.commit()

    now = datetime.utcnow()

    # 1) Force ACTIVE REHAB on p_rehab:
    #    days_total=7, rehab_start=3 -> consider rehab when days_remaining <= 3
    #    we set days_remaining=2 to be inside rehab
    rehab_injury = Injury(
        player_id=p_rehab.id,
        name="Test Rehab Strain",
        type="muscle",
        severity="moderate",
        start_date=now - timedelta(days=5),   # started 5 days ago
        days_total=7,                         # total duration
        rehab_start=3,                        # rehab starts in last 3 days
        rehab_xp_multiplier=0.5,              # not relevant for match sim, fine for debug
        fit_for_matches=False,
        days_remaining=2,                     # <= rehab_start (in rehab window)
    )
    session.add(rehab_injury)

    # 2) Force RECENTLY HEALED on p_recent:
    #    healed = start_date + days_total
    #    Make healed happen within RECENT_HEALED_WINDOW_DAYS
    days_total_recent = 5
    days_since_healed = min(RECENT_HEALED_WINDOW_DAYS, 3)  # healed 3 days ago
    recent_start = now - timedelta(days=(days_total_recent + days_since_healed))
    recent_injury = Injury(
        player_id=p_recent.id,
        name="Test Recent Knock",
        type="impact",
        severity="minor",
        start_date=recent_start,
        days_total=days_total_recent,
        rehab_start=1,
        rehab_xp_multiplier=0.8,
        fit_for_matches=True,
        days_remaining=0,  # healed
    )
    session.add(recent_injury)

    # 3) Force LOW ENERGY on p_low:
    p_low.energy = 10  # well below typical threshold (e.g., 50)

    session.commit()

    return {
        "ok": True,
        "club_id": club_id,
        "players": {
            "rehab": {"id": p_rehab.id, "name": f"{p_rehab.first_name} {p_rehab.last_name}"},
            "recent": {"id": p_recent.id, "name": f"{p_recent.first_name} {p_recent.last_name}"},
            "low_energy": {"id": p_low.id, "name": f"{p_low.first_name} {p_low.last_name}", "energy": p_low.energy},
        },
        "note": "Run /simulate with this club in a match. Check injury_risk_debug for multipliers and reasons.",
    }

from pydantic import BaseModel
from tactera_backend.models.player_model import Player
from tactera_backend.models.suspension_model import Suspension
from tactera_backend.core.database import get_session
from sqlmodel import Session

class SuspendRequest(BaseModel):
    player_id: int
    matches: int = 1
    reason: str = "debug"

@router.post("/debug/suspend-player")
def debug_suspend_player(data: SuspendRequest, session: Session = Depends(get_session)):
    """
    DEBUG: Create or update a suspension for a player.
    - If a Suspension exists, we set matches_remaining to 'matches'.
    - Otherwise we create one.
    """
    player = session.get(Player, data.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if there is an existing suspension entry; reuse or create
    active = None
    if player.suspensions:
        for sus in player.suspensions:
            # Reuse first entry (debug convenience)
            active = sus
            break

    if active:
        active.matches_remaining = data.matches
        active.reason = data.reason
    else:
        active = Suspension(
            player_id=player.id,
            reason=data.reason,
            matches_remaining=data.matches
        )
        session.add(active)

    session.commit()
    session.refresh(active)

    return {
        "message": "Suspension set",
        "player_id": player.id,
        "matches_remaining": active.matches_remaining,
        "reason": active.reason
    }

# ==========================================
# DEBUG: SUBSTITUTION SYSTEM TESTING
# ==========================================

@router.post("/debug/create-match-squad")
async def debug_create_match_squad(
    match_id: int,
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Manually create a match squad for testing substitutions.
    Selects first 18 available players for squad, first 11 for starting XI.
    """
    # Get available players for this club
    result = await db.execute(
        select(Player).where(Player.club_id == club_id).limit(18)
    )
    players = result.scalars().all()
    
    if len(players) < 11:
        raise HTTPException(status_code=400, detail=f"Club needs at least 11 players, found {len(players)}")
    
    # Check if match squad already exists
    existing = await db.execute(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    )
    existing_squad = existing.scalar_one_or_none()
    
    if existing_squad:
        return {
            "message": "Match squad already exists",
            "match_squad_id": existing_squad.id,
            "selected_players": existing_squad.selected_players,
            "starting_xi": existing_squad.starting_xi
        }
    
    # Create new match squad
    squad_players = [p.id for p in players]
    starting_players = squad_players[:11]  # First 11 as starting XI
    
    match_squad = MatchSquad(
        match_id=match_id,
        club_id=club_id,
        selected_players=squad_players,
        starting_xi=starting_players,
        substitutions_made=0,
        players_substituted=0,
        is_finalized=False
    )
    
    db.add(match_squad)
    await db.commit()
    await db.refresh(match_squad)
    
    return {
        "message": "Match squad created successfully",
        "match_squad_id": match_squad.id,
        "squad_size": len(squad_players),
        "starting_xi_size": len(starting_players),
        "selected_players": squad_players,
        "starting_xi": starting_players
    }


@router.post("/debug/make-test-substitution")
async def debug_make_test_substitution(
    match_id: int,
    club_id: int,
    player_off: int,
    player_on: int,
    minute: int = 60,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Make a simple test substitution.
    Useful for testing the substitution validation and creation logic.
    """
    # Create substitution request
    substitution_request = SubstitutionRequest(
        player_changes=[{"off": player_off, "on": player_on}],
        minute=minute,
        reason="debug_test"
    )
    
    # Use the validation function from substitution_routes
    with Session(sync_engine) as session:
        validation = validate_substitution_request(match_id, club_id, substitution_request, session)
    
    if not validation.is_valid:
        return {
            "success": False,
            "validation_errors": validation.errors,
            "warnings": validation.warnings
        }
    
    # Create the substitution if valid
    match_squad = await db.execute(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    )
    match_squad = match_squad.scalar_one_or_none()
    
    if not match_squad:
        raise HTTPException(status_code=404, detail="Match squad not found")
    
    # Create substitution record
    substitution = MatchSubstitution(
        match_id=match_id,
        club_id=club_id,
        substitution_number=match_squad.substitutions_made + 1,
        minute=minute,
        player_changes=[{"off": player_off, "on": player_on}],
        reason="debug_test"
    )
    
    db.add(substitution)
    
    # Update counters
    match_squad.substitutions_made += 1
    match_squad.players_substituted += 1
    db.add(match_squad)
    
    await db.commit()
    await db.refresh(substitution)
    
    return {
        "success": True,
        "substitution_id": substitution.id,
        "substitution_number": substitution.substitution_number,
        "minute": substitution.minute,
        "player_changes": substitution.player_changes,
        "remaining_substitutions": 3 - match_squad.substitutions_made,
        "remaining_player_changes": 5 - match_squad.players_substituted
    }


@router.get("/debug/match-squad/{match_id}/{club_id}")
async def debug_get_match_squad_details(
    match_id: int,
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Get detailed information about a match squad and its substitutions.
    """
    # Get match squad
    result = await db.execute(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    )
    match_squad = result.scalar_one_or_none()
    
    if not match_squad:
        return {"error": "Match squad not found"}
    
    # Get substitutions
    substitutions_result = await db.execute(
        select(MatchSubstitution).where(
            MatchSubstitution.match_id == match_id,
            MatchSubstitution.club_id == club_id
        ).order_by(MatchSubstitution.substitution_number)
    )
    substitutions = substitutions_result.scalars().all()
    
    # Get player details
    all_player_ids = set(match_squad.selected_players)
    for sub in substitutions:
        for change in sub.player_changes:
            all_player_ids.add(change["off"])
            all_player_ids.add(change["on"])
    
    players_result = await db.execute(
        select(Player).where(Player.id.in_(all_player_ids))
    )
    players = {p.id: f"{p.first_name} {p.last_name}" for p in players_result.scalars()}
    
    # Calculate current state
    substituted_off = set()
    substituted_on = set()
    
    for sub in substitutions:
        for change in sub.player_changes:
            substituted_off.add(change["off"])
            substituted_on.add(change["on"])
    
    current_on_pitch = set(match_squad.starting_xi) - substituted_off | substituted_on
    
    return {
        "match_squad": {
            "id": match_squad.id,
            "match_id": match_squad.match_id,
            "club_id": match_squad.club_id,
            "selected_players": match_squad.selected_players,
            "starting_xi": match_squad.starting_xi,
            "substitutions_made": match_squad.substitutions_made,
            "players_substituted": match_squad.players_substituted,
            "is_finalized": match_squad.is_finalized
        },
        "substitutions": [
            {
                "id": sub.id,
                "substitution_number": sub.substitution_number,
                "minute": sub.minute,
                "player_changes": sub.player_changes,
                "reason": sub.reason
            }
            for sub in substitutions
        ],
        "current_state": {
            "players_on_pitch": list(current_on_pitch),
            "players_on_pitch_names": [players.get(pid, f"Player {pid}") for pid in current_on_pitch],
            "substituted_off": list(substituted_off),
            "substituted_off_names": [players.get(pid, f"Player {pid}") for pid in substituted_off],
            "substituted_on": list(substituted_on),
            "substituted_on_names": [players.get(pid, f"Player {pid}") for pid in substituted_on]
        },
        "player_names": players
    }


@router.post("/debug/simulate-match-with-substitutions/{fixture_id}")
async def debug_simulate_match_with_substitutions(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Simulate a match using the new substitution-aware simulation.
    """
    from tactera_backend.core.match_sim import simulate_match_with_substitutions
    
    try:
        result = await simulate_match_with_substitutions(db, fixture_id)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Match simulation failed: {str(e)}")


@router.get("/debug/substitution-validation/{match_id}/{club_id}")
async def debug_substitution_validation(
    match_id: int,
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Check substitution validation status for a club in a match.
    """
    from tactera_backend.core.database import get_session
    
    # Use sync session for validation function
    with Session(sync_engine) as session:
        dummy_request = SubstitutionRequest(player_changes=[], minute=45)
        validation = validate_substitution_request(match_id, club_id, dummy_request, session)
    
    return {
        "match_id": match_id,
        "club_id": club_id,
        "validation": {
            "is_valid": validation.is_valid,
            "can_substitute": validation.can_substitute,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "remaining_substitutions": validation.remaining_substitutions,
            "remaining_player_changes": validation.remaining_player_changes
        }
    }
    
    # ==========================================
# DEBUG: TRANSFER COMPLETION TESTING
# ==========================================

@router.post("/debug/complete-transfers")
async def debug_complete_transfers(db: AsyncSession = Depends(get_db)):
    """
    DEBUG: Manually trigger transfer completion for all expired auctions.
    Useful for testing the transfer system.
    """
    from tactera_backend.services.transfer_completion_service import process_expired_auctions
    
    result = await process_expired_auctions(db)
    return result


@router.post("/debug/expire-auction/{listing_id}")
async def debug_expire_auction(listing_id: int, db: AsyncSession = Depends(get_db)):
    """
    DEBUG: Manually expire an auction for testing.
    Sets the auction end time to 1 minute ago.
    """
    from tactera_backend.models.contract_model import TransferListing
    from datetime import datetime, timedelta
    
    listing = await db.get(TransferListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Transfer listing not found")
    
    # Set auction to expire 1 minute ago
    listing.auction_end = datetime.utcnow() - timedelta(minutes=1)
    db.add(listing)
    await db.commit()
    
    return {
        "message": f"Auction {listing_id} expired for testing",
        "auction_end": listing.auction_end,
        "note": "Use /debug/complete-transfers to trigger completion"
    }


@router.get("/debug/transfer-status")
async def debug_transfer_status(db: AsyncSession = Depends(get_db)):
    """
    DEBUG: Get overview of all transfer activity.
    Shows active, expired, and completed auctions.
    """
    from tactera_backend.models.contract_model import TransferListing, AuctionStatus
    from sqlmodel import select
    
    # Get all transfer listings by status
    result = await db.execute(select(TransferListing))
    all_listings = result.scalars().all()
    
    status_counts = {}
    expired_but_active = []
    
    for listing in all_listings:
        status = listing.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Check for expired auctions that haven't been processed
        if (listing.status == AuctionStatus.ACTIVE and 
            listing.auction_end < datetime.utcnow()):
            expired_but_active.append({
                "listing_id": listing.id,
                "player_id": listing.player_id,
                "expired_minutes_ago": int((datetime.utcnow() - listing.auction_end).total_seconds() / 60),
                "current_bid": listing.current_bid
            })
    
    return {
        "total_listings": len(all_listings),
        "status_breakdown": status_counts,
        "expired_but_not_processed": len(expired_but_active),
        "expired_details": expired_but_active
    }

@router.post("/debug/create-match-squad")
async def debug_create_match_squad(
    match_id: int,
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Manually create a match squad for testing substitutions.
    Selects first 18 available players for squad, first 11 for starting XI.
    """
    # Get available players for this club
    result = await db.execute(
        select(Player).where(Player.club_id == club_id).limit(18)
    )
    players = result.scalars().all()
    
    if len(players) < 11:
        raise HTTPException(status_code=400, detail=f"Club needs at least 11 players, found {len(players)}")
    
    # Check if match squad already exists
    existing = await db.execute(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    )
    existing_squad = existing.scalar_one_or_none()
    
    if existing_squad:
        return {
            "message": "Match squad already exists",
            "match_squad_id": existing_squad.id,
            "selected_players": existing_squad.selected_players,
            "starting_xi": existing_squad.starting_xi
        }
    
    # Create new match squad
    squad_players = [p.id for p in players]
    starting_players = squad_players[:11]  # First 11 as starting XI
    
    match_squad = MatchSquad(
        match_id=match_id,
        club_id=club_id,
        selected_players=squad_players,
        starting_xi=starting_players,
        substitutions_made=0,
        players_substituted=0,
        is_finalized=False
    )
    
    db.add(match_squad)
    await db.commit()
    await db.refresh(match_squad)
    
    return {
        "message": "Match squad created successfully",
        "match_squad_id": match_squad.id,
        "squad_size": len(squad_players),
        "starting_xi_size": len(starting_players),
        "selected_players": squad_players,
        "starting_xi": starting_players
    }


@router.post("/debug/make-test-substitution")
async def debug_make_test_substitution(
    match_id: int,
    club_id: int,
    player_off: int,
    player_on: int,
    minute: int = 60,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Make a simple test substitution.
    Useful for testing the substitution validation and creation logic.
    """
    # Create substitution request
    substitution_request = SubstitutionRequest(
        player_changes=[{"off": player_off, "on": player_on}],
        minute=minute,
        reason="debug_test"
    )
    
    # Use the validation function from substitution_routes
    with Session(sync_engine) as session:
        validation = validate_substitution_request(match_id, club_id, substitution_request, session)
    
    if not validation.is_valid:
        return {
            "success": False,
            "validation_errors": validation.errors,
            "warnings": validation.warnings
        }
    
    # Create the substitution if valid
    match_squad = await db.execute(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    )
    match_squad = match_squad.scalar_one_or_none()
    
    if not match_squad:
        raise HTTPException(status_code=404, detail="Match squad not found")
    
    # Create substitution record
    substitution = MatchSubstitution(
        match_id=match_id,
        club_id=club_id,
        substitution_number=match_squad.substitutions_made + 1,
        minute=minute,
        player_changes=[{"off": player_off, "on": player_on}],
        reason="debug_test"
    )
    
    db.add(substitution)
    
    # Update counters
    match_squad.substitutions_made += 1
    match_squad.players_substituted += 1
    db.add(match_squad)
    
    await db.commit()
    await db.refresh(substitution)
    
    return {
        "success": True,
        "substitution_id": substitution.id,
        "substitution_number": substitution.substitution_number,
        "minute": substitution.minute,
        "player_changes": substitution.player_changes,
        "remaining_substitutions": 3 - match_squad.substitutions_made,
        "remaining_player_changes": 5 - match_squad.players_substituted
    }


@router.get("/debug/match-squad/{match_id}/{club_id}")
async def debug_get_match_squad_details(
    match_id: int,
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Get detailed information about a match squad and its substitutions.
    """
    # Get match squad
    result = await db.execute(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    )
    match_squad = result.scalar_one_or_none()
    
    if not match_squad:
        return {"error": "Match squad not found"}
    
    # Get substitutions
    substitutions_result = await db.execute(
        select(MatchSubstitution).where(
            MatchSubstitution.match_id == match_id,
            MatchSubstitution.club_id == club_id
        ).order_by(MatchSubstitution.substitution_number)
    )
    substitutions = substitutions_result.scalars().all()
    
    # Get player details
    all_player_ids = set(match_squad.selected_players)
    for sub in substitutions:
        for change in sub.player_changes:
            all_player_ids.add(change["off"])
            all_player_ids.add(change["on"])
    
    players_result = await db.execute(
        select(Player).where(Player.id.in_(all_player_ids))
    )
    players = {p.id: f"{p.first_name} {p.last_name}" for p in players_result.scalars()}
    
    # Calculate current state
    substituted_off = set()
    substituted_on = set()
    
    for sub in substitutions:
        for change in sub.player_changes:
            substituted_off.add(change["off"])
            substituted_on.add(change["on"])
    
    current_on_pitch = set(match_squad.starting_xi) - substituted_off | substituted_on
    
    return {
        "match_squad": {
            "id": match_squad.id,
            "match_id": match_squad.match_id,
            "club_id": match_squad.club_id,
            "selected_players": match_squad.selected_players,
            "starting_xi": match_squad.starting_xi,
            "substitutions_made": match_squad.substitutions_made,
            "players_substituted": match_squad.players_substituted,
            "is_finalized": match_squad.is_finalized
        },
        "substitutions": [
            {
                "id": sub.id,
                "substitution_number": sub.substitution_number,
                "minute": sub.minute,
                "player_changes": sub.player_changes,
                "reason": sub.reason
            }
            for sub in substitutions
        ],
        "current_state": {
            "players_on_pitch": list(current_on_pitch),
            "players_on_pitch_names": [players.get(pid, f"Player {pid}") for pid in current_on_pitch],
            "substituted_off": list(substituted_off),
            "substituted_off_names": [players.get(pid, f"Player {pid}") for pid in substituted_off],
            "substituted_on": list(substituted_on),
            "substituted_on_names": [players.get(pid, f"Player {pid}") for pid in substituted_on]
        },
        "player_names": players
    }


@router.post("/debug/simulate-match-with-substitutions/{fixture_id}")
async def debug_simulate_match_with_substitutions(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Simulate a match using the new substitution-aware simulation.
    """
    from tactera_backend.core.match_sim import simulate_match_with_substitutions
    
    try:
        result = await simulate_match_with_substitutions(db, fixture_id)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Match simulation failed: {str(e)}")


@router.get("/debug/substitution-validation/{match_id}/{club_id}")
async def debug_substitution_validation(
    match_id: int,
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG: Check substitution validation status for a club in a match.
    """
    from tactera_backend.core.database import get_session
    
    # Use sync session for validation function
    with Session(sync_engine) as session:
        dummy_request = SubstitutionRequest(player_changes=[], minute=45)
        validation = validate_substitution_request(match_id, club_id, dummy_request, session)
    
    return {
        "match_id": match_id,
        "club_id": club_id,
        "validation": {
            "is_valid": validation.is_valid,
            "can_substitute": validation.can_substitute,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "remaining_substitutions": validation.remaining_substitutions,
            "remaining_player_changes": validation.remaining_player_changes
        }
    }
    
@router.post("/debug/create-contracts-for-all-players")
def debug_create_contracts(session: Session = Depends(get_session)):
    """
    DEBUG: Create contracts for all players who don't have one.
    """
    from tactera_backend.models.contract_model import PlayerContract
    from datetime import date, timedelta
    import random
    
    # Get all players without contracts
    players_without_contracts = session.exec(
        select(Player).where(
            ~Player.id.in_(select(PlayerContract.player_id))
        )
    ).all()
    
    contracts_created = 0
    for player in players_without_contracts:
        contract = PlayerContract(
            player_id=player.id,
            club_id=player.club_id,
            daily_wage=random.randint(100, 300),
            contract_expires=date.today() + timedelta(days=random.randint(30, 365)),
            auto_generated=False
        )
        session.add(contract)
        contracts_created += 1
    
    session.commit()
    
    return {
        "message": f"Created {contracts_created} contracts",
        "contracts_created": contracts_created
    }
    
@router.post("/debug/create-free-agents")
def debug_create_free_agents(
    count: int = 5,
    session: Session = Depends(get_session)
):
    """
    DEBUG: Create some players without contracts to test the free agent system.
    """
    from tactera_backend.models.player_model import Player
    from tactera_backend.models.contract_model import PlayerContract
    import random
    
    positions = ["GK", "LB", "CB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]
    preferred_feet = ["left", "right", "both"]
    
    free_agents_created = []
    
    for i in range(count):
        # Create a player without a club (club_id = None won't work, so we'll use club_id = 1 then remove contract)
        position = random.choice(positions)
        is_goalkeeper = position == "GK"
        
        player = Player(
            first_name=f"Free{i+1}",
            last_name="Agent",
            age=random.randint(18, 32),
            position=position,
            height_cm=random.randint(165, 195),
            weight_kg=random.randint(65, 85),
            preferred_foot=random.choice(preferred_feet),
            is_goalkeeper=is_goalkeeper,
            ambition=random.randint(40, 90),
            consistency=random.randint(30, 85),
            injury_proneness=random.randint(15, 50),
            potential=random.randint(60, 120),
            club_id=None,  # No club - true free agent!
            energy=random.randint(80, 100)
        )
        
        session.add(player)
        session.commit()
        session.refresh(player)
        
        # Don't create a contract - this makes them a free agent!
        free_agents_created.append({
            "id": player.id,
            "name": f"{player.first_name} {player.last_name}",
            "position": player.position,
            "age": player.age
        })
    
    return {
        "message": f"Created {count} free agents for testing",
        "free_agents": free_agents_created
    }
    
@router.post("/debug/expire-contracts")
def debug_expire_contracts(
    count: int = 3,
    session: Session = Depends(get_session)
):
    """
    DEBUG: Expire some player contracts to create free agents.
    """
    from tactera_backend.models.contract_model import PlayerContract
    from datetime import date, timedelta
    
    # Get some random contracts to expire
    contracts = session.exec(select(PlayerContract).limit(count * 2)).all()
    
    expired_players = []
    expired_count = 0
    
    for contract in contracts:
        if expired_count >= count:
            break
            
        # Set contract to have expired today
        contract.contract_expires = date.today()
        session.add(contract)
        
        player = session.get(Player, contract.player_id)
        if player:
            expired_players.append({
                "id": player.id,
                "name": f"{player.first_name} {player.last_name}",
                "expired_date": contract.contract_expires
            })
            expired_count += 1
    
    session.commit()
    
    return {
        "message": f"Expired {expired_count} contracts to create contract expiry auctions",
        "expired_players": expired_players
    }