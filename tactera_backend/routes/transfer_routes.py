# tactera_backend/routes/transfer_routes.py
# API routes for transfer market and contract management

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta, date

from tactera_backend.core.database import get_session, get_db
from tactera_backend.models.contract_model import (
    PlayerContract, TransferListing, TransferBid, ContractPreference,
    TransferType, AuctionStatus, ContractRead, TransferListingRead,
    CreateAuctionRequest, CreateTransferListRequest, PlaceBidRequest,
    TransferBidRead, ContractOfferRequest, ContractOfferResponse
)
from tactera_backend.models.player_model import Player
from tactera_backend.models.club_model import Club

router = APIRouter()

# ==========================================
# TRANSFER MARKET - VIEW ACTIVE AUCTIONS
# ==========================================

@router.get("/auctions", response_model=List[TransferListingRead])
def get_active_auctions(
    max_price: Optional[int] = None,
    position: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Get all active auctions (traditional auctions and triggered transfer list auctions).
    Only includes listings that have active bidding with time limits.
    """
    # Get auctions that are either AUCTION type or TRANSFER_LIST with bids
    query = select(TransferListing).where(
        TransferListing.status == AuctionStatus.ACTIVE,
        (
            (TransferListing.transfer_type == TransferType.AUCTION) |
            ((TransferListing.transfer_type == TransferType.TRANSFER_LIST) & (TransferListing.current_bid > 0))
        )
    )
    
    # Apply filters
    if max_price:
        query = query.where(TransferListing.asking_price <= max_price)
    
    listings = session.exec(query).all()
    
    # Filter by position if specified
    if position:
        filtered_listings = []
        for listing in listings:
            player = session.get(Player, listing.player_id)
            if player and player.position.lower() == position.lower():
                filtered_listings.append(listing)
        listings = filtered_listings
    
    # Convert to response format with minutes remaining
    result = []
    for listing in listings:
        now = datetime.utcnow()
        minutes_remaining = max(0, int((listing.auction_end - now).total_seconds() / 60))
        
        listing_dict = listing.__dict__.copy()
        listing_dict['minutes_remaining'] = minutes_remaining
        
        listing_data = TransferListingRead(**listing_dict)
        result.append(listing_data)
    
    # Sort by auction end time (soonest first)
    result.sort(key=lambda x: x.auction_end)
    
    return result


@router.get("/transfer-list")
def get_transfer_list(
    max_price: Optional[int] = None,
    position: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Get all players on the transfer list (VMan style).
    These are players with asking prices that haven't been triggered yet.
    """
    # Get transfer list entries that haven't been triggered (no bids yet)
    query = select(TransferListing).where(
        TransferListing.status == AuctionStatus.ACTIVE,
        TransferListing.transfer_type == TransferType.TRANSFER_LIST,
        TransferListing.current_bid == 0
    )
    
    # Apply filters
    if max_price:
        query = query.where(TransferListing.asking_price <= max_price)
    
    listings = session.exec(query).all()
    
    # Filter by position if specified
    if position:
        filtered_listings = []
        for listing in listings:
            player = session.get(Player, listing.player_id)
            if player and player.position.lower() == position.lower():
                filtered_listings.append(listing)
        listings = filtered_listings
    
    # Convert to response format (no minutes_remaining needed)
    result = []
    for listing in listings:
        player = session.get(Player, listing.player_id)
        selling_club = session.get(Club, listing.club_id)
        
        result.append({
            "listing_id": listing.id,
            "player": {
                "id": player.id,
                "name": f"{player.first_name} {player.last_name}",
                "age": player.age,
                "position": player.position,
                "energy": player.energy
            },
            "selling_club": {
                "id": selling_club.id,
                "name": selling_club.name
            },
            "asking_price": listing.asking_price,
            "listed_date": listing.created_at
        })
    
    # Sort by asking price (lowest first)
    result.sort(key=lambda x: x["asking_price"])
    
    return result


@router.get("/market")
def get_all_transfer_activity(
    session: Session = Depends(get_session)
):
    """
    Get both active auctions and transfer list in one response.
    Provides complete overview of transfer market activity.
    """
    # Get auctions (with time limits)
    auctions_query = select(TransferListing).where(
        TransferListing.status == AuctionStatus.ACTIVE,
        (
            (TransferListing.transfer_type == TransferType.AUCTION) |
            ((TransferListing.transfer_type == TransferType.TRANSFER_LIST) & (TransferListing.current_bid > 0))
        )
    )
    auctions = session.exec(auctions_query).all()
    
    # Get transfer list (no time limits)
    transfer_list_query = select(TransferListing).where(
        TransferListing.status == AuctionStatus.ACTIVE,
        TransferListing.transfer_type == TransferType.TRANSFER_LIST,
        TransferListing.current_bid == 0
    )
    transfer_list = session.exec(transfer_list_query).all()
    
    # Format auctions
    auction_data = []
    for listing in auctions:
        now = datetime.utcnow()
        minutes_remaining = max(0, int((listing.auction_end - now).total_seconds() / 60))
        
        player = session.get(Player, listing.player_id)
        selling_club = session.get(Club, listing.club_id)
        
        auction_data.append({
            "listing_id": listing.id,
            "type": "auction",
            "player": {
                "id": player.id,
                "name": f"{player.first_name} {player.last_name}",
                "age": player.age,
                "position": player.position
            },
            "selling_club": selling_club.name,
            "current_bid": listing.current_bid,
            "minutes_remaining": minutes_remaining,
            "bid_count": listing.bid_count
        })
    
    # Format transfer list
    transfer_list_data = []
    for listing in transfer_list:
        player = session.get(Player, listing.player_id)
        selling_club = session.get(Club, listing.club_id)
        
        transfer_list_data.append({
            "listing_id": listing.id,
            "type": "transfer_list",
            "player": {
                "id": player.id,
                "name": f"{player.first_name} {player.last_name}",
                "age": player.age,
                "position": player.position
            },
            "selling_club": selling_club.name,
            "asking_price": listing.asking_price
        })
    
    return {
        "active_auctions": auction_data,
        "transfer_list": transfer_list_data,
        "total_auctions": len(auction_data),
        "total_transfer_list": len(transfer_list_data)
    }


@router.get("/market/{listing_id}")
def get_transfer_listing_details(
    listing_id: int,
    session: Session = Depends(get_session)
):
    """
    Get detailed information about a specific transfer listing.
    Includes player details and bid history.
    """
    listing = session.get(TransferListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Transfer listing not found")
    
    # Get player details
    player = session.get(Player, listing.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get selling club
    selling_club = session.get(Club, listing.club_id)
    
    # Get bid history
    bids = session.exec(
        select(TransferBid)
        .where(TransferBid.transfer_listing_id == listing_id)
        .order_by(TransferBid.bid_time.desc())
    ).all()
    
    # Calculate time remaining
    now = datetime.utcnow()
    minutes_remaining = max(0, int((listing.auction_end - now).total_seconds() / 60))
    
    return {
    "listing": {
        "id": listing.id,
        "player_id": listing.player_id,
        "club_id": listing.club_id,
        "transfer_type": listing.transfer_type.value,
        "asking_price": listing.asking_price,
        "auction_end": listing.auction_end,
        "status": listing.status.value,
        "current_bid": listing.current_bid,
        "current_bidder_id": listing.current_bidder_id,
        "bid_count": listing.bid_count,
        "minutes_remaining": minutes_remaining,
        "winning_bid": listing.winning_bid,
        "winning_club_id": listing.winning_club_id,
        "transfer_completed": listing.transfer_completed
    },
    "player": {
        "id": player.id,
        "name": f"{player.first_name} {player.last_name}",
        "age": player.age,
        "position": player.position,
        "energy": player.energy
    },
    "selling_club": {
        "id": selling_club.id,
        "name": selling_club.name
    } if selling_club else None,
    "bids": [TransferBidRead.from_orm(bid) for bid in bids[:10]]  # Last 10 bids
}


# ==========================================
# TRANSFER MARKET - CREATE LISTINGS
# ==========================================

@router.post("/auction")
def create_auction(
    request: CreateAuctionRequest,
    session: Session = Depends(get_session)
):
    """
    Create a traditional auction for a player.
    Manager sets starting price and auction duration.
    """
    # Validate player ownership
    player = session.get(Player, request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # TODO: Add manager authentication to verify club ownership
    # For now, assume the club_id comes from the authenticated manager
    club_id = player.club_id  # Placeholder until auth is implemented
    
    # Check if player is already listed
    existing_listing = session.exec(
        select(TransferListing).where(
            TransferListing.player_id == request.player_id,
            TransferListing.status == AuctionStatus.ACTIVE
        )
    ).first()
    
    if existing_listing:
        raise HTTPException(status_code=400, detail="Player is already on the transfer market")
    
    # Check if player has active contract
    contract = session.exec(
        select(PlayerContract).where(PlayerContract.player_id == request.player_id)
    ).first()
    
    if not contract:
        raise HTTPException(status_code=400, detail="Player must have a contract to be transferred")
    
    # Calculate auction end time
    auction_end = datetime.utcnow() + timedelta(minutes=request.auction_duration_minutes)
    
    # Create auction listing
    listing = TransferListing(
        player_id=request.player_id,
        club_id=club_id,
        transfer_type=TransferType.AUCTION,
        asking_price=request.starting_price,
        auction_end=auction_end,
        auction_duration_minutes=request.auction_duration_minutes,
        current_bid=request.starting_price,
        status=AuctionStatus.ACTIVE
    )
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return {
        "message": "Auction created successfully",
        "listing_id": listing.id,
        "auction_end": listing.auction_end,
        "starting_price": listing.asking_price
    }


@router.post("/transfer-list")
def create_transfer_list(
    request: CreateTransferListRequest,
    session: Session = Depends(get_session)
):
    """
    Add player to transfer list (VMan style).
    If someone bids the asking price, triggers 15-minute auction.
    """
    # Validate player ownership
    player = session.get(Player, request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # TODO: Add manager authentication
    club_id = player.club_id  # Placeholder
    
    # Check if player is already listed
    existing_listing = session.exec(
        select(TransferListing).where(
            TransferListing.player_id == request.player_id,
            TransferListing.status == AuctionStatus.ACTIVE
        )
    ).first()
    
    if existing_listing:
        raise HTTPException(status_code=400, detail="Player is already on the transfer market")
    
    # Create transfer list entry (no auction yet)
    listing = TransferListing(
        player_id=request.player_id,
        club_id=club_id,
        transfer_type=TransferType.TRANSFER_LIST,
        asking_price=request.asking_price,
        auction_end=datetime.utcnow() + timedelta(days=7),  # Placeholder, will be updated when auction triggered
        auction_duration_minutes=15,  # Fixed 15 minutes for transfer list auctions
        current_bid=0,  # No bids yet
        status=AuctionStatus.ACTIVE
    )
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return {
        "message": "Player added to transfer list successfully",
        "listing_id": listing.id,
        "asking_price": listing.asking_price,
        "transfer_type": "transfer_list"
    }


# ==========================================
# TRANSFER MARKET - BIDDING
# ==========================================

@router.post("/bid/{listing_id}")
def place_bid(
    listing_id: int,
    request: PlaceBidRequest,
    session: Session = Depends(get_session)
):
    """
    Place a bid on a transfer listing.
    Handles both regular auctions and transfer list triggers.
    """
    listing = session.get(TransferListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Transfer listing not found")
    
    if listing.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Auction is not active")
    
    # TODO: Get bidding club from authenticated manager
    # For now, assume we get it from request or session
    bidding_club_id = 1  # Placeholder until auth implemented
    
    # Validate bid amount
    minimum_bid = listing.current_bid + 1 if listing.current_bid > 0 else listing.asking_price
    
    if request.bid_amount < minimum_bid:
        raise HTTPException(
            status_code=400, 
            detail=f"Bid must be at least {minimum_bid}"
        )
    
    # Check if this is a transfer list trigger
    if listing.transfer_type == TransferType.TRANSFER_LIST and listing.current_bid == 0:
        if request.bid_amount >= listing.asking_price:
            # Trigger 15-minute auction
            listing.auction_end = datetime.utcnow() + timedelta(minutes=15)
            listing.triggered_by_club_id = bidding_club_id
            listing.current_bid = request.bid_amount
            listing.current_bidder_id = bidding_club_id
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Transfer list requires minimum bid of {listing.asking_price}"
            )
    else:
        # Regular bid on active auction
        listing.current_bid = request.bid_amount
        listing.current_bidder_id = bidding_club_id
        
        # Check for auction extension (if bid in last 5 minutes)
        time_remaining = listing.auction_end - datetime.utcnow()
        if time_remaining.total_seconds() < 300:  # Less than 5 minutes
            # Extend auction by 5 minutes
            listing.auction_end = datetime.utcnow() + timedelta(minutes=5)
    
    # Create bid record
    bid = TransferBid(
        transfer_listing_id=listing_id,
        bidding_club_id=bidding_club_id,
        bid_amount=request.bid_amount,
        is_winning=True
    )
    
    # Mark previous bids as not winning
    previous_bids = session.exec(
        select(TransferBid).where(
            TransferBid.transfer_listing_id == listing_id,
            TransferBid.is_winning == True
        )
    ).all()
    
    for prev_bid in previous_bids:
        prev_bid.is_winning = False
        session.add(prev_bid)
    
    listing.bid_count += 1
    session.add(listing)
    session.add(bid)
    session.commit()
    session.refresh(bid)
    
    # Calculate new time remaining
    now = datetime.utcnow()
    minutes_remaining = max(0, int((listing.auction_end - now).total_seconds() / 60))
    
    response = {
        "message": "Bid placed successfully",
        "bid_id": bid.id,
        "new_highest_bid": listing.current_bid,
        "minutes_remaining": minutes_remaining
    }
    
    # Add special message for transfer list triggers
    if listing.transfer_type == TransferType.TRANSFER_LIST and listing.triggered_by_club_id == bidding_club_id:
        response["message"] = "Transfer list auction triggered! 15-minute auction started."
        response["auction_triggered"] = True
    
    return response


# ==========================================
# CONTRACT MANAGEMENT
# ==========================================

@router.get("/contracts/{player_id}")
def get_player_contract(
    player_id: int,
    session: Session = Depends(get_session)
):
    """
    Get a player's current contract details.
    """
    contract = session.exec(
        select(PlayerContract).where(PlayerContract.player_id == player_id)
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Player contract not found")
    
    # Calculate days remaining
    today = date.today()
    days_remaining = (contract.contract_expires - today).days
    
    return {
        "player_id": contract.player_id,
        "club_id": contract.club_id,
        "daily_wage": contract.daily_wage,
        "contract_start": contract.contract_start,
        "contract_expires": contract.contract_expires,
        "days_remaining": days_remaining,
        "preference_type": contract.preference_type.value,
        "auto_generated": contract.auto_generated
    }


# ==========================================
# TRANSFER COMPLETION (HELPER ENDPOINT)
# ==========================================

@router.post("/complete/{listing_id}")
async def complete_transfer(
    listing_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete a transfer when auction ends.
    This would normally be called by a background job.
    """
    from tactera_backend.services.transfer_completion_service import complete_single_auction
    
    listing = await db.get(TransferListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Transfer listing not found")
    
    if listing.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Transfer is not active")
    
    # Check if auction has ended
    if datetime.utcnow() < listing.auction_end:
        raise HTTPException(status_code=400, detail="Auction has not ended yet")
    
    try:
        result = await complete_single_auction(db, listing)
        await db.commit()
        return result
    except Exception as e:
        await db.rollback()
        print(f"Transfer completion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transfer completion failed: {str(e)}")


@router.post("/contracts/offer")
def offer_contract(
    request: ContractOfferRequest,
    session: Session = Depends(get_session)
):
    """
    Offer a new contract to a player.
    For now, auto-accepts all reasonable offers.
    """
    player = session.get(Player, request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if player already has a contract
    existing_contract = session.exec(
        select(PlayerContract).where(PlayerContract.player_id == request.player_id)
    ).first()
    
    if existing_contract:
        # Update existing contract
        existing_contract.daily_wage = request.daily_wage
        existing_contract.contract_expires = date.today() + timedelta(days=request.contract_length_days)
        existing_contract.updated_at = datetime.utcnow()
        existing_contract.auto_generated = False
        
        session.add(existing_contract)
        session.commit()
        
        return {
            "message": "Contract updated successfully",
            "accepted": True,
            "daily_wage": request.daily_wage,
            "contract_expires": existing_contract.contract_expires
        }
    else:
        raise HTTPException(status_code=404, detail="Player must have an existing contract to renew")