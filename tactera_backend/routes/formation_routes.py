# tactera_backend/routes/formation_routes.py
# API routes for formation and lineup management

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any
from tactera_backend.core.database import get_session
from tactera_backend.models.formation_model import (
    FormationTemplate, ClubFormation, FormationTemplateRead, 
    ClubFormationRead, FormationUpdateRequest
)
from tactera_backend.models.club_model import Club
from tactera_backend.models.player_model import Player
from datetime import datetime

router = APIRouter()

# ==========================================
# GET ALL FORMATION TEMPLATES
# ==========================================
@router.get("/templates", response_model=List[FormationTemplateRead])
def get_formation_templates(session: Session = Depends(get_session)):
    """
    Get all available formation templates (4-4-2, 3-5-2, etc.)
    These are the base formations clubs can choose from.
    """
    templates = session.exec(
        select(FormationTemplate).where(FormationTemplate.is_active == True)
    ).all()
    
    return templates


# ==========================================
# GET CLUB'S CURRENT FORMATION
# ==========================================
@router.get("/club/{club_id}/current")
def get_club_formation(club_id: int, session: Session = Depends(get_session)):
    """
    Get a club's current active formation with player assignments.
    Returns formation template info + assigned players.
    """
    # 1. Verify club exists
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # 2. Get the club's active formation
    club_formation = session.exec(
        select(ClubFormation).where(
            ClubFormation.club_id == club_id,
            ClubFormation.is_active == True
        )
    ).first()
    
    if not club_formation:
        # No formation set - return empty state
        return {
            "club_id": club_id,
            "club_name": club.name,
            "has_formation": False,
            "message": "No formation set for this club"
        }
    
    # 3. Get the formation template details
    template = session.get(FormationTemplate, club_formation.formation_template_id)
    
    # 4. Get player details for assigned positions
    assigned_players = {}
    if club_formation.player_assignments:
        player_ids = list(club_formation.player_assignments.values())
        if player_ids:
            players = session.exec(
                select(Player).where(Player.id.in_(player_ids))
            ).all()
            player_dict = {p.id: p for p in players}
            
            # Build position -> player mapping
            for position, player_id in club_formation.player_assignments.items():
                if player_id in player_dict:
                    p = player_dict[player_id]
                    assigned_players[position] = {
                        "id": p.id,
                        "name": f"{p.first_name} {p.last_name}",
                        "position": p.position,
                        "energy": p.energy
                    }
    
    return {
        "club_id": club_id,
        "club_name": club.name,
        "has_formation": True,
        "formation": {
            "id": club_formation.id,
            "template_id": template.id if template else None,
            "template_name": template.name if template else "Unknown",
            "template_positions": template.positions if template else {},
            "player_assignments": club_formation.player_assignments,
            "assigned_players": assigned_players,
            "mentality": club_formation.mentality,
            "pressing": club_formation.pressing,
            "tempo": club_formation.tempo,
            "name": club_formation.name,
            "captain_id": club_formation.captain_id,
            "penalty_taker_id": club_formation.penalty_taker_id,
            "free_kick_taker_id": club_formation.free_kick_taker_id
        }
    }


# ==========================================
# SET CLUB'S FORMATION TEMPLATE
# ==========================================
@router.post("/club/{club_id}/set-template/{template_id}")
def set_club_formation_template(
    club_id: int, 
    template_id: int, 
    session: Session = Depends(get_session)
):
    """
    Set a club's formation template (e.g., switch from 4-4-2 to 3-5-2).
    This creates a new ClubFormation or updates the existing one.
    Player assignments are cleared when changing templates.
    """
    # 1. Verify club and template exist
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    template = session.get(FormationTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Formation template not found")
    
    # 2. Check if club already has a formation
    existing_formation = session.exec(
        select(ClubFormation).where(
            ClubFormation.club_id == club_id,
            ClubFormation.is_active == True
        )
    ).first()
    
    if existing_formation:
        # Update existing formation
        existing_formation.formation_template_id = template_id
        existing_formation.player_assignments = {}  # Clear assignments
        existing_formation.updated_at = datetime.utcnow()
        existing_formation.name = f"{template.name} Formation"
        session.add(existing_formation)
    else:
        # Create new formation
        new_formation = ClubFormation(
            club_id=club_id,
            formation_template_id=template_id,
            player_assignments={},
            name=f"{template.name} Formation"
        )
        session.add(new_formation)
    
    session.commit()
    
    return {
        "message": f"Formation template set to {template.name}",
        "club_id": club_id,
        "template_id": template_id,
        "template_name": template.name
    }


# ==========================================
# ASSIGN PLAYER TO POSITION
# ==========================================
@router.post("/club/{club_id}/assign-player")
def assign_player_to_position(
    club_id: int,
    position: str,
    player_id: int,
    session: Session = Depends(get_session)
):
    """
    Assign a specific player to a formation position.
    Example: Assign Player #5 to "CB1" position.
    """
    # 1. Verify club exists
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # 2. Verify player exists and belongs to this club
    player = session.get(Player, player_id)
    if not player or player.club_id != club_id:
        raise HTTPException(status_code=404, detail="Player not found or doesn't belong to this club")
    
    # 3. Get the club's formation
    club_formation = session.exec(
        select(ClubFormation).where(
            ClubFormation.club_id == club_id,
            ClubFormation.is_active == True
        )
    ).first()
    
    if not club_formation:
        raise HTTPException(status_code=400, detail="Club has no formation set. Set a formation template first.")
    
    # 4. Verify position exists in the formation template
    template = session.get(FormationTemplate, club_formation.formation_template_id)
    if not template or position not in template.positions:
        raise HTTPException(status_code=400, detail=f"Position '{position}' not found in current formation")
    
    # 5. Remove player from any existing position (prevent duplicates)
    if club_formation.player_assignments:
        current_assignments = club_formation.player_assignments.copy()
        for pos, pid in current_assignments.items():
            if pid == player_id:
                del current_assignments[pos]
        club_formation.player_assignments = current_assignments
    else:
        club_formation.player_assignments = {}
    
    # 6. Assign player to new position
    club_formation.player_assignments[position] = player_id
    club_formation.updated_at = datetime.utcnow()
    
    session.add(club_formation)
    session.commit()
    
    return {
        "message": f"Player {player.first_name} {player.last_name} assigned to {position}",
        "club_id": club_id,
        "position": position,
        "player_id": player_id,
        "player_name": f"{player.first_name} {player.last_name}"
    }


# ==========================================
# REMOVE PLAYER FROM POSITION
# ==========================================
@router.delete("/club/{club_id}/remove-player/{position}")
def remove_player_from_position(
    club_id: int,
    position: str,
    session: Session = Depends(get_session)
):
    """
    Remove a player from a specific formation position.
    """
    # 1. Get the club's formation
    club_formation = session.exec(
        select(ClubFormation).where(
            ClubFormation.club_id == club_id,
            ClubFormation.is_active == True
        )
    ).first()
    
    if not club_formation:
        raise HTTPException(status_code=404, detail="Club formation not found")
    
    # 2. Remove player from position if assigned
    if club_formation.player_assignments and position in club_formation.player_assignments:
        removed_player_id = club_formation.player_assignments.pop(position)
        club_formation.updated_at = datetime.utcnow()
        
        session.add(club_formation)
        session.commit()
        
        return {
            "message": f"Player removed from {position}",
            "position": position,
            "removed_player_id": removed_player_id
        }
    else:
        raise HTTPException(status_code=404, detail=f"No player assigned to position '{position}'")


# ==========================================
# GET CLUB SQUAD FOR FORMATION BUILDING
# ==========================================
@router.get("/club/{club_id}/available-players")
def get_available_players_for_formation(club_id: int, session: Session = Depends(get_session)):
    """
    Get all players available for formation assignment.
    Includes injury status and current formation assignment.
    """
    # 1. Verify club exists
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # 2. Get all players in the squad
    players = session.exec(
        select(Player).where(Player.club_id == club_id)
    ).all()
    
    # 3. Get current formation assignments
    club_formation = session.exec(
        select(ClubFormation).where(
            ClubFormation.club_id == club_id,
            ClubFormation.is_active == True
        )
    ).first()
    
    assigned_positions = {}
    if club_formation and club_formation.player_assignments:
        # Reverse mapping: player_id -> position
        for position, player_id in club_formation.player_assignments.items():
            assigned_positions[player_id] = position
    
    # 4. Build response with availability info
    available_players = []
    for player in players:
        # TODO: Add injury check when injury system is integrated
        is_injured = False  # Placeholder
        
        available_players.append({
            "id": player.id,
            "name": f"{player.first_name} {player.last_name}",
            "position": player.position,
            "energy": player.energy,
            "is_injured": is_injured,
            "assigned_to": assigned_positions.get(player.id),  # None if not assigned
            "is_available": not is_injured  # Could add more criteria later
        })
    
    return {
        "club_id": club_id,
        "club_name": club.name,
        "players": available_players
    }