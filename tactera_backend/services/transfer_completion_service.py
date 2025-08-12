# tactera_backend/services/transfer_completion_service.py
# Background service to automatically complete expired transfer auctions

import asyncio
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from tactera_backend.core.database import engine
from tactera_backend.models.contract_model import (
    TransferListing, TransferBid, PlayerContract, AuctionStatus
)
from tactera_backend.models.player_model import Player
from tactera_backend.models.club_model import Club

async def process_expired_auctions(db: AsyncSession) -> dict:
    """
    Find and complete all expired auctions.
    Returns summary of completed transfers.
    """
    now = datetime.utcnow()
    
    # Find all active auctions that have expired
    result = await db.execute(
        select(TransferListing).where(
            TransferListing.status == AuctionStatus.ACTIVE,
            TransferListing.auction_end <= now
        )
    )
    expired_auctions = result.scalars().all()
    
    if not expired_auctions:
        return {
            "message": "No expired auctions to process",
            "completed_transfers": 0,
            "failed_auctions": 0,
            "transfers": []
        }
    
    completed_transfers = []
    failed_auctions = []
    
    for listing in expired_auctions:
        try:
            transfer_result = await complete_single_auction(db, listing)
            if transfer_result["status"] == "completed":
                completed_transfers.append(transfer_result)
            else:
                failed_auctions.append(transfer_result)
        except Exception as e:
            print(f"Error completing auction {listing.id}: {str(e)}")
            failed_auctions.append({
                "listing_id": listing.id,
                "status": "error",
                "error": str(e)
            })
    
    await db.commit()
    
    return {
        "message": f"Processed {len(expired_auctions)} expired auctions",
        "completed_transfers": len(completed_transfers),
        "failed_auctions": len(failed_auctions),
        "transfers": completed_transfers
    }


async def complete_single_auction(db: AsyncSession, listing: TransferListing) -> dict:
    """
    Complete a single auction transfer.
    Handles player transfer, contract creation, and payment.
    """
    # Get the winning bid
    result = await db.execute(
        select(TransferBid).where(
            TransferBid.transfer_listing_id == listing.id,
            TransferBid.is_winning == True
        )
    )
    winning_bid = result.scalar_one_or_none()
    
    if not winning_bid:
        # No bids - check if this was a contract expiry auction
        player = await db.get(Player, listing.player_id)
        
        if listing.asking_price == 1 and listing.auction_duration_minutes == 1440:
            # This was a contract expiry auction with no bids - player stays as free agent
            # (Player is already club_id = None from when contract expired)
            
            listing.status = AuctionStatus.EXPIRED
            db.add(listing)
            
            return {
                "listing_id": listing.id,
                "status": "expired", 
                "reason": "No bids received - player remained free agent",
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                "became_free_agent": True
            }
        else:
            # Regular auction with no bids
            listing.status = AuctionStatus.EXPIRED
            db.add(listing)
            
            return {
                "listing_id": listing.id,
                "status": "expired",
                "reason": "No bids received"
            }
    
    # Get player and clubs
    player = await db.get(Player, listing.player_id)
    selling_club = await db.get(Club, listing.club_id)
    buying_club = await db.get(Club, winning_bid.bidding_club_id)
    
    if not player or not selling_club or not buying_club:
        listing.status = AuctionStatus.CANCELLED
        db.add(listing)
        
        return {
            "listing_id": listing.id,
            "status": "error",
            "reason": "Missing player or club data"
        }
    
    # Check squad limits for buying club
    current_squad_result = await db.execute(
        select(Player).where(Player.club_id == buying_club.id)
    )
    current_squad_size = len(current_squad_result.scalars().all())
    
    # Check if buying club has pending outgoing transfers that would free space
    pending_sales_result = await db.execute(
        select(TransferListing).where(
            TransferListing.club_id == buying_club.id,
            TransferListing.status == AuctionStatus.ACTIVE,
            TransferListing.current_bid > 0,
            TransferListing.auction_end <= datetime.utcnow() + timedelta(hours=1)
        )
    )
    pending_sales = len(pending_sales_result.scalars().all())
    
    effective_squad_size = current_squad_size - pending_sales
    
    if effective_squad_size >= 25:
        if effective_squad_size >= 26:
            listing.status = AuctionStatus.CANCELLED
            db.add(listing)
            
            return {
                "listing_id": listing.id,
                "status": "cancelled",
                "reason": f"Buying club squad full ({current_squad_size} players, max 26)"
            }
    
    old_club_id = player.club_id
    new_club_id = buying_club.id
    transfer_fee = winning_bid.bid_amount
    
    # Transfer the player
    player.club_id = new_club_id
    
    # =========================================
    # 💰 NEW: Transfer money between clubs
    # =========================================
    # Check if buying club has enough money
    if buying_club.money < transfer_fee:
        # Cancel transfer due to insufficient funds
        listing.status = AuctionStatus.CANCELLED
        db.add(listing)
        
        return {
            "listing_id": listing.id,
            "status": "cancelled",
            "reason": f"Buying club insufficient funds (has ${buying_club.money:,}, needs ${transfer_fee:,})",
            "buying_club": buying_club.name,
            "shortfall": transfer_fee - buying_club.money
        }

    # Execute money transfer
    buying_club.money -= transfer_fee
    selling_club.money += transfer_fee

    # Log the financial transaction
    financial_info = {
        "transfer_fee": transfer_fee,
        "buying_club_before": buying_club.money + transfer_fee,  # What they had before
        "buying_club_after": buying_club.money,
        "selling_club_before": selling_club.money - transfer_fee,  # What they had before  
        "selling_club_after": selling_club.money
    }

    # Save club money changes
    db.add(buying_club)
    db.add(selling_club)

    print(f"💰 Transfer fee: ${transfer_fee:,} from {buying_club.name} to {selling_club.name}")

    # Handle contract - update existing or create new
    old_contract_result = await db.execute(
        select(PlayerContract).where(PlayerContract.player_id == player.id)
    )
    old_contract = old_contract_result.scalar_one_or_none()

    if old_contract:
        # Update existing contract instead of creating new one
        old_contract.club_id = new_club_id
        old_contract.daily_wage = 100
        old_contract.contract_expires = date.today() + timedelta(days=3)
        old_contract.auto_generated = True
        old_contract.updated_at = datetime.utcnow()
        db.add(old_contract)
        print(f"Updated existing contract for player {player.id}")
    else:
        # Create new contract only if none exists
        new_contract = PlayerContract(
            player_id=player.id,
            club_id=new_club_id,
            daily_wage=100,
            contract_expires=date.today() + timedelta(days=3),
            auto_generated=True
        )
        db.add(new_contract)
        print(f"Created new contract for player {player.id}")

    # Update auction status
    listing.status = AuctionStatus.COMPLETED
    listing.winning_bid = transfer_fee
    listing.winning_club_id = new_club_id
    listing.transfer_completed = True
    listing.updated_at = datetime.utcnow()

    # Save all changes
    db.add(player)
    db.add(listing)
    # Contract is already added in the if/else block above
    
    return {
    "listing_id": listing.id,
    "status": "completed",
    "player_id": player.id,
    "player_name": f"{player.first_name} {player.last_name}",
    "from_club": selling_club.name,
    "to_club": buying_club.name,
    "transfer_fee": transfer_fee,
    "winning_bid_id": winning_bid.id,
    "financial_transaction": financial_info  # NEW: Include financial details
    }

async def run_transfer_completion_loop():
    """
    Background loop that checks for expired auctions every minute.
    """
    while True:
        try:
            async with AsyncSession(engine) as session:
                result = await process_expired_auctions(session)
                
                if result["completed_transfers"] > 0 or result["failed_auctions"] > 0:
                    print(f"[{datetime.utcnow()}] Transfer completion: {result['completed_transfers']} completed, {result['failed_auctions']} expired")
                
        except Exception as e:
            print(f"[{datetime.utcnow()}] Transfer completion error: {str(e)}")
        
        # Wait 1 minute before checking again
        await asyncio.sleep(60)


# Manual trigger for testing
async def trigger_transfer_completion():
    """
    Manually trigger transfer completion - useful for testing.
    """
    async with AsyncSession(engine) as session:
        return await process_expired_auctions(session)