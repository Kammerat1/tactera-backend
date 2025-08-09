# tactera_backend/routes/substitution_routes.py
# API routes for match substitutions

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from tactera_backend.core.database import get_session
from tactera_backend.models.formation_model import (
    MatchSquad, MatchSubstitution, SubstitutionRequest, SubstitutionRead,
    MatchSquadRead, SubstitutionValidationResponse
)
from tactera_backend.models.match_model import Match
from tactera_backend.models.club_model import Club
from tactera_backend.models.player_model import Player
from tactera_backend.models.injury_model import Injury
from tactera_backend.models.suspension_model import Suspension

router = APIRouter()

# ==========================================
# SUBSTITUTION VALIDATION HELPER
# ==========================================

def validate_substitution_request(
    match_id: int, 
    club_id: int, 
    substitution_request: SubstitutionRequest, 
    session: Session
) -> SubstitutionValidationResponse:
    """
    Validates a substitution request against FIFA rules and game state.
    
    Rules:
    - Maximum 3 substitution events per team per match
    - Maximum 5 players can be changed per team per match  
    - Substituted players cannot return to the match
    - Only bench players can be substituted in
    - Players being substituted out must be on the pitch
    """
    errors = []
    warnings = []
    
    # 1. Check if match exists and is in progress
    match = session.get(Match, match_id)
    if not match:
        errors.append("Match not found")
        return SubstitutionValidationResponse(
            is_valid=False, can_substitute=False, errors=errors, warnings=warnings,
            remaining_substitutions=0, remaining_player_changes=0
        )
    
    if match.is_played:
        errors.append("Cannot make substitutions in a completed match")
    
    # 2. Get match squad for this club
    match_squad = session.exec(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    ).first()
    
    if not match_squad:
        errors.append("Match squad not found for this club")
        return SubstitutionValidationResponse(
            is_valid=False, can_substitute=False, errors=errors, warnings=warnings,
            remaining_substitutions=0, remaining_player_changes=0
        )
    
    # 3. Check substitution limits
    remaining_substitutions = 3 - match_squad.substitutions_made
    remaining_player_changes = 5 - match_squad.players_substituted
    
    if remaining_substitutions <= 0:
        errors.append("Maximum substitution events (3) already used")
    
    if len(substitution_request.player_changes) > remaining_player_changes:
        errors.append(f"Cannot substitute {len(substitution_request.player_changes)} players. Only {remaining_player_changes} changes remaining")
    
    # 4. Get current substitution history to track who's been substituted
    substitutions = session.exec(
        select(MatchSubstitution).where(
            MatchSubstitution.match_id == match_id,
            MatchSubstitution.club_id == club_id
        )
    ).all()
    
    # Build sets of players who are off/on the pitch
    substituted_off = set()  # Players who have been substituted off
    substituted_on = set()   # Players who have been substituted on
    
    for sub in substitutions:
        for change in sub.player_changes:
            substituted_off.add(change["off"])
            substituted_on.add(change["on"])
    
    # Current players on pitch = starting XI - substituted off + substituted on
    current_on_pitch = set(match_squad.starting_xi) - substituted_off | substituted_on
    
    # 5. Validate each player change
    for change in substitution_request.player_changes:
        player_off = change.get("off")
        player_on = change.get("on")
        
        if not player_off or not player_on:
            errors.append("Each substitution must specify both 'off' and 'on' players")
            continue
        
        # Check player being substituted off
        if player_off not in current_on_pitch:
            errors.append(f"Player {player_off} is not currently on the pitch")
        
        if player_off in substituted_off:
            errors.append(f"Player {player_off} has already been substituted off")
        
        # Check player being substituted on
        if player_on not in match_squad.selected_players:
            errors.append(f"Player {player_on} is not in the match squad")
        
        if player_on in current_on_pitch:
            errors.append(f"Player {player_on} is already on the pitch")
        
        if player_on in substituted_on:
            errors.append(f"Player {player_on} has already been substituted on")
        
        # Check player availability (injuries, suspensions)
        player = session.get(Player, player_on)
        if player:
            # Check for active injury that prevents match play
            active_injury = session.exec(
                select(Injury).where(
                    Injury.player_id == player_on,
                    Injury.days_remaining > 0,
                    Injury.fit_for_matches == False
                )
            ).first()
            
            if active_injury:
                errors.append(f"Player {player_on} is injured and not fit for matches")
            
            # Check for active suspension
            active_suspension = session.exec(
                select(Suspension).where(
                    Suspension.player_id == player_on,
                    Suspension.matches_remaining > 0
                )
            ).first()
            
            if active_suspension:
                errors.append(f"Player {player_on} is suspended")
    
    # 6. Check minute validity
    if substitution_request.minute < 0 or substitution_request.minute > 120:
        errors.append("Substitution minute must be between 0 and 120")
    
    # 7. Generate warnings for tactical considerations
    if substitution_request.minute < 10:
        warnings.append("Very early substitution - consider if this is intended")
    
    if len(substitution_request.player_changes) > 1:
        warnings.append("Multiple simultaneous substitutions - ensure this is tactically sound")
    
    is_valid = len(errors) == 0
    can_substitute = is_valid and remaining_substitutions > 0 and remaining_player_changes > 0
    
    return SubstitutionValidationResponse(
        is_valid=is_valid,
        can_substitute=can_substitute,
        errors=errors,
        warnings=warnings,
        remaining_substitutions=remaining_substitutions,
        remaining_player_changes=remaining_player_changes
    )


# ==========================================
# VALIDATE SUBSTITUTION (GET)
# ==========================================

@router.get("/matches/{match_id}/clubs/{club_id}/substitutions/validate")
def validate_substitution(
    match_id: int,
    club_id: int,
    session: Session = Depends(get_session)
) -> SubstitutionValidationResponse:
    """
    Check if a club can make substitutions in a match.
    Returns current substitution status and any limitations.
    """
    # Create a dummy request to validate general substitution ability
    dummy_request = SubstitutionRequest(player_changes=[], minute=45)
    
    result = validate_substitution_request(match_id, club_id, dummy_request, session)
    
    # Override specific errors since this is just a general check
    general_errors = [error for error in result.errors 
                     if "must specify both" not in error 
                     and "Cannot substitute 0 players" not in error]
    
    return SubstitutionValidationResponse(
        is_valid=len(general_errors) == 0,
        can_substitute=result.remaining_substitutions > 0 and result.remaining_player_changes > 0,
        errors=general_errors,
        warnings=result.warnings,
        remaining_substitutions=result.remaining_substitutions,
        remaining_player_changes=result.remaining_player_changes
    )


# ==========================================
# MAKE SUBSTITUTION (POST)
# ==========================================

@router.post("/matches/{match_id}/clubs/{club_id}/substitutions")
def make_substitution(
    match_id: int,
    club_id: int,
    substitution_request: SubstitutionRequest,
    session: Session = Depends(get_session)
) -> SubstitutionRead:
    """
    Execute a substitution during a match.
    
    Body should contain:
    - player_changes: [{"off": player_id, "on": player_id}, ...]
    - minute: Match minute when substitution occurs
    - reason: Optional reason for the substitution
    """
    
    # 1. Validate the substitution request
    validation = validate_substitution_request(match_id, club_id, substitution_request, session)
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "Substitution validation failed",
                "errors": validation.errors,
                "warnings": validation.warnings
            }
        )
    
    # 2. Get match squad to update counters
    match_squad = session.exec(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    ).first()
    
    # 3. Create the substitution record
    substitution = MatchSubstitution(
        match_id=match_id,
        club_id=club_id,
        substitution_number=match_squad.substitutions_made + 1,
        minute=substitution_request.minute,
        player_changes=substitution_request.player_changes,
        reason=substitution_request.reason
    )
    
    session.add(substitution)
    
    # 4. Update match squad counters
    match_squad.substitutions_made += 1
    match_squad.players_substituted += len(substitution_request.player_changes)
    
    session.add(match_squad)
    session.commit()
    session.refresh(substitution)
    
    return SubstitutionRead.from_orm(substitution)


# ==========================================
# GET MATCH SUBSTITUTIONS (GET)
# ==========================================

@router.get("/matches/{match_id}/clubs/{club_id}/substitutions", response_model=List[SubstitutionRead])
def get_match_substitutions(
    match_id: int,
    club_id: int,
    session: Session = Depends(get_session)
) -> List[SubstitutionRead]:
    """
    Get all substitutions made by a club in a specific match.
    """
    substitutions = session.exec(
        select(MatchSubstitution).where(
            MatchSubstitution.match_id == match_id,
            MatchSubstitution.club_id == club_id
        ).order_by(MatchSubstitution.substitution_number)
    ).all()
    
    return [SubstitutionRead.from_orm(sub) for sub in substitutions]


# ==========================================
# GET AVAILABLE SUBSTITUTES (GET)
# ==========================================

@router.get("/matches/{match_id}/clubs/{club_id}/available-substitutes")
def get_available_substitutes(
    match_id: int,
    club_id: int,
    session: Session = Depends(get_session)
):
    """
    Get players available for substitution (bench players who can come on).
    Also returns current players on the pitch who can be substituted off.
    """
    
    # 1. Get match squad
    match_squad = session.exec(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    ).first()
    
    if not match_squad:
        raise HTTPException(status_code=404, detail="Match squad not found")
    
    # 2. Get substitution history
    substitutions = session.exec(
        select(MatchSubstitution).where(
            MatchSubstitution.match_id == match_id,
            MatchSubstitution.club_id == club_id
        )
    ).all()
    
    # Track substitution changes
    substituted_off = set()
    substituted_on = set()
    
    for sub in substitutions:
        for change in sub.player_changes:
            substituted_off.add(change["off"])
            substituted_on.add(change["on"])
    
    # 3. Calculate current state
    current_on_pitch = set(match_squad.starting_xi) - substituted_off | substituted_on
    bench_players = set(match_squad.selected_players) - current_on_pitch - substituted_on
    
    # 4. Get player details
    all_relevant_players = list(current_on_pitch | bench_players)
    players = session.exec(
        select(Player).where(Player.id.in_(all_relevant_players))
    ).all()
    
    player_dict = {p.id: p for p in players}
    
    # 5. Build response
    on_pitch = []
    available_subs = []
    
    for player_id in current_on_pitch:
        if player_id in player_dict:
            p = player_dict[player_id]
            on_pitch.append({
                "id": p.id,
                "name": f"{p.first_name} {p.last_name}",
                "position": p.position,
                "energy": p.energy,
                "can_be_substituted": True  # Players on pitch can always be subbed off
            })
    
    for player_id in bench_players:
        if player_id in player_dict:
            p = player_dict[player_id]
            
            # Check availability (injuries, suspensions)
            can_substitute = True
            unavailable_reason = None
            
            # Check injury
            active_injury = session.exec(
                select(Injury).where(
                    Injury.player_id == player_id,
                    Injury.days_remaining > 0,
                    Injury.fit_for_matches == False
                )
            ).first()
            
            if active_injury:
                can_substitute = False
                unavailable_reason = f"Injured: {active_injury.name}"
            
            # Check suspension
            active_suspension = session.exec(
                select(Suspension).where(
                    Suspension.player_id == player_id,
                    Suspension.matches_remaining > 0
                )
            ).first()
            
            if active_suspension:
                can_substitute = False
                unavailable_reason = f"Suspended: {active_suspension.reason}"
            
            available_subs.append({
                "id": p.id,
                "name": f"{p.first_name} {p.last_name}",
                "position": p.position,
                "energy": p.energy,
                "can_substitute": can_substitute,
                "unavailable_reason": unavailable_reason
            })
    
    return {
        "match_id": match_id,
        "club_id": club_id,
        "substitutions_remaining": 3 - match_squad.substitutions_made,
        "player_changes_remaining": 5 - match_squad.players_substituted,
        "current_on_pitch": on_pitch,
        "available_substitutes": available_subs
    }


# ==========================================
# GET MATCH SQUAD WITH SUBSTITUTION STATUS (GET)
# ==========================================

@router.get("/matches/{match_id}/clubs/{club_id}/squad", response_model=MatchSquadRead)
def get_match_squad_with_substitutions(
    match_id: int,
    club_id: int,
    session: Session = Depends(get_session)
) -> MatchSquadRead:
    """
    Get the match squad with current substitution status.
    """
    match_squad = session.exec(
        select(MatchSquad).where(
            MatchSquad.match_id == match_id,
            MatchSquad.club_id == club_id
        )
    ).first()
    
    if not match_squad:
        raise HTTPException(status_code=404, detail="Match squad not found")
    
    return MatchSquadRead.from_orm(match_squad)