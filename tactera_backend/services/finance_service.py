# tactera_backend/services/finance_service.py
# Handles club financial operations like wage payments and transfers

from sqlmodel import Session, select
from tactera_backend.models.club_model import Club
from tactera_backend.models.contract_model import PlayerContract
from tactera_backend.models.player_model import Player
from datetime import date, datetime
from typing import Optional


def pay_daily_wages(session: Session, club_id: int) -> dict:
    """
    Pay daily wages for all players with active contracts at a club.
    Returns summary of payments made.
    """
    club = session.get(Club, club_id)
    if not club:
        raise ValueError(f"Club {club_id} not found")
    
    # Get all active contracts for this club
    active_contracts = session.exec(
        select(PlayerContract).where(
            PlayerContract.club_id == club_id,
            PlayerContract.contract_expires >= date.today()
        )
    ).all()
    
    total_wages = 0
    payments_made = []
    
    for contract in active_contracts:
        player = session.get(Player, contract.player_id)
        if player:
            total_wages += contract.daily_wage
            payments_made.append({
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                "daily_wage": contract.daily_wage
            })
    
    # Check if club can afford wages
    if club.money >= total_wages:
        club.money -= total_wages
        session.add(club)
        session.commit()
        
        return {
            "success": True,
            "total_wages": total_wages,
            "remaining_money": club.money,
            "payments_made": payments_made
        }
    else:
        return {
            "success": False,
            "total_wages": total_wages,
            "current_money": club.money,
            "shortfall": total_wages - club.money,
            "message": "Insufficient funds for wage payments"
        }


def transfer_money(session: Session, from_club_id: int, to_club_id: int, amount: int, reason: str = "transfer") -> dict:
    """
    Transfer money between clubs (for transfer fees).
    """
    from_club = session.get(Club, from_club_id)
    to_club = session.get(Club, to_club_id)
    
    if not from_club or not to_club:
        return {"success": False, "message": "Club not found"}
    
    if from_club.money < amount:
        return {
            "success": False, 
            "message": "Insufficient funds",
            "required": amount,
            "available": from_club.money
        }
    
    # Execute transfer
    from_club.money -= amount
    to_club.money += amount
    
    session.add(from_club)
    session.add(to_club)
    session.commit()
    
    return {
        "success": True,
        "amount": amount,
        "from_club": from_club.name,
        "to_club": to_club.name,
        "reason": reason,
        "from_club_remaining": from_club.money,
        "to_club_new_total": to_club.money
    }


def add_revenue(session: Session, club_id: int, amount: int, source: str = "match_revenue") -> dict:
    """
    Add revenue to a club (from match attendance, prizes, etc.).
    """
    club = session.get(Club, club_id)
    if not club:
        return {"success": False, "message": "Club not found"}
    
    club.money += amount
    session.add(club)
    session.commit()
    
    return {
        "success": True,
        "amount": amount,
        "source": source,
        "new_total": club.money
    }


def get_club_finances(session: Session, club_id: int) -> dict:
    """
    Get detailed financial information for a club.
    """
    club = session.get(Club, club_id)
    if not club:
        return {"error": "Club not found"}
    
    # Calculate daily wage expenses
    active_contracts = session.exec(
        select(PlayerContract).where(
            PlayerContract.club_id == club_id,
            PlayerContract.contract_expires >= date.today()
        )
    ).all()
    
    daily_wages = sum(contract.daily_wage for contract in active_contracts)
    
    # Calculate days until bankruptcy (if only paying wages)
    days_until_bankruptcy = club.money // daily_wages if daily_wages > 0 else float('inf')
    
    return {
        "club_id": club_id,
        "club_name": club.name,
        "current_money": club.money,
        "daily_wage_expenses": daily_wages,
        "active_contracts": len(active_contracts),
        "days_until_bankruptcy": int(days_until_bankruptcy) if days_until_bankruptcy != float('inf') else None,
        "financial_status": "healthy" if days_until_bankruptcy > 30 else "warning" if days_until_bankruptcy > 7 else "critical"
    }