# tactera_backend/routes/free_agent_routes.py
# API routes for free agent market - instant signings with sign-on fees only

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import date, timedelta, datetime

from tactera_backend.core.database import get_session
from tactera_backend.models.contract_model import (
    PlayerContract, FreeAgentRead, SignFreeAgentRequest, SignFreeAgentResponse,
    is_free_agent
)
from tactera_backend.models.player_model import Player
from tactera_backend.models.club_model import Club

router = APIRouter()

# ==========================================
# GET ALL FREE AGENTS
# ==========================================

@router.get("/", response_model=List[FreeAgentRead])
def get_free_agents(session: Session = Depends(get_session)):
    """
    Get all players who are currently free agents.
    These players have no active contracts and can be signed instantly.
    """
    # Get all players
    all_players = session.exec(select(Player)).all()
    
    free_agents = []
    
    for player in all_players:
        if is_free_agent(player.id, session):
            # Calculate how long they've been free
            last_contract = session.exec(
                select(PlayerContract)
                .where(PlayerContract.player_id == player.id)
                .order_by(PlayerContract.updated_at.desc())
            ).first()
            
            if last_contract and last_contract.contract_expires:
                days_since_free = (date.today() - last_contract.contract_expires).days
            else:
                days_since_free = 999  # Never had a contract
            
            # Calculate suggested sign-on fee based on player attributes
            base_fee = 500  # Base sign-on fee
            age_factor = max(0.5, 1.0 - (player.age - 20) * 0.02)  # Younger = higher fee
            asking_price = int(base_fee * age_factor)
            
            free_agents.append(FreeAgentRead(
                player_id=player.id,
                name=f"{player.first_name} {player.last_name}",
                age=player.age,
                position=player.position,
                energy=player.energy,
                asking_price=asking_price,
                days_since_free=max(0, days_since_free)
            ))
    
    # Sort by asking price (cheapest first)
    free_agents.sort(key=lambda x: x.asking_price)
    
    return free_agents


# ==========================================
# SIGN FREE AGENT (INSTANT)
# ==========================================

@router.post("/sign/{player_id}")
def sign_free_agent(
    player_id: int,
    request: SignFreeAgentRequest,
    session: Session = Depends(get_session)
) -> SignFreeAgentResponse:
    """
    Instantly sign a free agent with a sign-on fee and contract terms.
    No auction - immediate signing if the player accepts the offer.
    """
    
    # 1. Verify player exists and is a free agent
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if not is_free_agent(player_id, session):
        raise HTTPException(status_code=400, detail="Player is not a free agent")
    
    # 2. TODO: Get signing club from authenticated manager
    # For now, use a placeholder club
    signing_club_id = 1  # Replace with actual club from auth
    
    signing_club = session.get(Club, signing_club_id)
    if not signing_club:
        raise HTTPException(status_code=404, detail="Signing club not found")
    
    # 3. Check if signing club has squad space
    current_squad = session.exec(
        select(Player).where(Player.club_id == signing_club_id)
    ).all()
    
    if len(current_squad) >= 25:
        raise HTTPException(
            status_code=400, 
            detail=f"Squad is full ({len(current_squad)}/25 players)"
        )
    
    # 4. Simple acceptance logic (can be made more complex later)
    # For now, players accept reasonable offers
    min_acceptable_fee = 100
    min_acceptable_wage = 75
    
    if request.sign_on_fee < min_acceptable_fee:
        raise HTTPException(
            status_code=400,
            detail=f"Sign-on fee too low. Player wants at least {min_acceptable_fee}"
        )
    
    if request.daily_wage < min_acceptable_wage:
        raise HTTPException(
            status_code=400,
            detail=f"Daily wage too low. Player wants at least {min_acceptable_wage}"
        )
    
    # 5. Complete the signing
    # Transfer player to new club
    player.club_id = signing_club_id
    
    # Create new contract
    contract_expires = date.today() + timedelta(days=request.contract_length_days)
    
    new_contract = PlayerContract(
        player_id=player_id,
        club_id=signing_club_id,
        daily_wage=request.daily_wage,
        contract_start=date.today(),
        contract_expires=contract_expires,
        auto_generated=False  # This was a negotiated signing
    )
    
    session.add(player)
    session.add(new_contract)
    session.commit()
    
    return SignFreeAgentResponse(
        success=True,
        player_name=f"{player.first_name} {player.last_name}",
        sign_on_fee=request.sign_on_fee,
        daily_wage=request.daily_wage,
        contract_expires=contract_expires,
        message=f"Successfully signed {player.first_name} {player.last_name}!"
    )


# ==========================================
# GET FREE AGENT DETAILS
# ==========================================

@router.get("/{player_id}")
def get_free_agent_details(
    player_id: int,
    session: Session = Depends(get_session)
):
    """
    Get detailed information about a specific free agent.
    """
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if not is_free_agent(player_id, session):
        raise HTTPException(status_code=400, detail="Player is not a free agent")
    
    # Get last club information
    last_contract = session.exec(
        select(PlayerContract)
        .where(PlayerContract.player_id == player_id)
        .order_by(PlayerContract.updated_at.desc())
    ).first()
    
    last_club_name = "Never had a club"
    days_since_free = 999
    
    if last_contract:
        last_club = session.get(Club, last_contract.club_id)
        if last_club:
            last_club_name = last_club.name
        
        if last_contract.contract_expires:
            days_since_free = (date.today() - last_contract.contract_expires).days
    
    # Calculate market value suggestion
    base_fee = 500
    age_factor = max(0.5, 1.0 - (player.age - 20) * 0.02)
    suggested_fee = int(base_fee * age_factor)
    
    return {
        "player": {
            "id": player.id,
            "name": f"{player.first_name} {player.last_name}",
            "age": player.age,
            "position": player.position,
            "height_cm": player.height_cm,
            "weight_kg": player.weight_kg,
            "preferred_foot": player.preferred_foot,
            "energy": player.energy
        },
        "free_agent_info": {
            "days_since_free": max(0, days_since_free),
            "last_club": last_club_name,
            "suggested_sign_on_fee": suggested_fee,
            "min_acceptable_wage": 75,
            "max_contract_length": 365
        }
    }