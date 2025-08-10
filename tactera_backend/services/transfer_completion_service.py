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
        # No bids - auction failed
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
    # Count current players in buying club
    current_squad_result = await db.execute(
        select(Player).where(Player.club_id == buying_club.id)
    )
    current_squad_size = len(current_squad_result.scalars().all())
    
    # Check if buying club has pending outgoing transfers that would free space
    pending_sales_result = await db.execute(
        select(TransferListing).where(
            TransferListing.club_id == buying_club.id,
            TransferListing.status == AuctionStatus.ACTIVE,
            TransferListing.current_bid > 0,  # Has active bids
            TransferListing.auction_end <= datetime.utcnow() + timedelta(hours=1)  # Ends soon
        )
    )
    pending_sales = len(pending_sales_result.scalars().all())
    
    effective_squad_size = current_squad_size - pending_sales
    
    if effective_squad_size >= 25:
        # Check if this would exceed the temporary 26 limit
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
    
    # Handle old contract
    old_contract_result = await db.execute(
        select(PlayerContract).where(PlayerContract.player_id == player.id)
    )
    old_contract = old_contract_result.scalar_one_or_none()
    
    if old_contract:
        # Delete old contract
        await db.delete(old_contract)
    
    # Create new 3-day auto-contract
    new_contract = PlayerContract(
        player_id=player.id,
        club_id=new_club_id,
        daily_wage=100,  # Default wage for auto-contract
        contract_expires=date.today() + timedelta(days=3),
        auto_generated=True
    )
    
    # Update auction status
    listing.status = AuctionStatus.COMPLETED
    listing.winning_bid = transfer_fee
    listing.winning_club_id = new_club_id
    listing.transfer_completed = True
    listing.updated_at = datetime.utcnow()
    
    # Apply transfer fee (simplified for now - just subtract from buying club)
    # TODO: Add proper financial system
    # buying_club.balance -= transfer_fee
    # selling_club.balance += transfer_fee * 0.95  # 5% transaction fee
    
    # Save all changes
    db.add(player)
    db.add(new_contract)
    db.add(listing)
    # db.add(buying_club)  # Uncomment when financial system exists
    # db.add(selling_club)
    
    return {
        "listing_id": listing.id,
        "status": "completed",
        "player_id": player.id,
        "player_name": f"{player.first_name} {player.last_name}",
        "from_club": selling_club.name,
        "to_club": buying_club.name,
        "transfer_fee": transfer_fee,
        "winning_bid_id": winning_bid.id
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
                    print(f"[{datetime.utcnow()}] Transfer completion: {result['completed_transfers']} completed, {result['failed_auctions']} failed")
                
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