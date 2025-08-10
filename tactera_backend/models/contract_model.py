# tactera_backend/models/contract_model.py
# Defines player contracts and transfer system models

from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime, date
from pydantic import BaseModel
from enum import Enum
from tactera_backend.models.club_model import Club
from tactera_backend.models.player_model import Player

def is_free_agent(player_id: int, session) -> bool:
    """
    Check if a player is a free agent (no club or no active contract).
    """
    from sqlmodel import select
    from tactera_backend.models.player_model import Player
    
    # Get the player
    player = session.get(Player, player_id)
    if not player:
        return False
    
    # If player has no club, they're definitely a free agent
    if player.club_id is None:
        return True
    
    # If player has a club, they're not a free agent
    return False

class ContractPreference(str, Enum):
    """Player preferences for contract terms"""
    SECURITY_FOCUSED = "security_focused"  # Prefers longer contracts, lower wages
    MONEY_FOCUSED = "money_focused"        # Prefers shorter contracts, higher wages
    BALANCED = "balanced"                  # No strong preference

class TransferType(str, Enum):
    """Type of transfer listing"""
    AUCTION = "auction"           # Traditional auction with start price and duration
    TRANSFER_LIST = "transfer_list"  # VMan-style: asking price triggers 15-min auction

class AuctionStatus(str, Enum):
    """Current status of an auction"""
    ACTIVE = "active"             # Auction is running, accepting bids
    COMPLETED = "completed"       # Auction finished, winner determined
    CANCELLED = "cancelled"       # Auction was cancelled by seller
    EXPIRED = "expired"          # No bids received, auction expired

# ==========================================
# PLAYER CONTRACT MODEL
# ==========================================

class PlayerContract(SQLModel, table=True):
    """
    Tracks a player's current contract with their club.
    Each player has exactly one active contract at a time.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", unique=True)  # One active contract per player
    club_id: int = Field(foreign_key="club.id")
    
    # Contract terms
    daily_wage: int = Field(default=100, description="Daily wage in game currency")
    contract_start: date = Field(default_factory=date.today)
    contract_expires: date = Field(description="Date when contract expires")
    
    # Player preferences (affects contract negotiations)
    preference_type: ContractPreference = Field(default=ContractPreference.BALANCED)
    
    # Metadata
    auto_generated: bool = Field(default=False, description="True if 3-day auto-contract from transfer")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    player: Optional["Player"] = Relationship(back_populates="current_contract")
    club: Optional["Club"] = Relationship()

# ==========================================
# TRANSFER LISTING MODEL
# ==========================================

class TransferListing(SQLModel, table=True):
    """
    Represents a player being offered for sale via auction or transfer list.
    Supports both VMan-style systems: traditional auctions and transfer list.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    club_id: int = Field(foreign_key="club.id")  # Selling club
    
    # Transfer details
    transfer_type: TransferType = Field(description="Auction or transfer list")
    asking_price: int = Field(description="Starting price (auction) or asking price (transfer list)")
    
    # Auction timing
    auction_start: datetime = Field(default_factory=datetime.utcnow)
    auction_end: datetime = Field(description="When auction closes")
    auction_duration_minutes: int = Field(description="Original auction length in minutes")
    
    # Current auction state
    status: AuctionStatus = Field(default=AuctionStatus.ACTIVE)
    current_bid: int = Field(default=0, description="Current highest bid")
    current_bidder_id: Optional[int] = Field(default=None, foreign_key="club.id")
    bid_count: int = Field(default=0, description="Total number of bids placed")
    
    # Transfer list specific (VMan system)
    triggered_by_club_id: Optional[int] = Field(default=None, foreign_key="club.id", 
                                               description="Club that triggered transfer list auction")
    
    # Result tracking
    winning_bid: Optional[int] = Field(default=None, description="Final winning bid amount")
    winning_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    transfer_completed: bool = Field(default=False)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    player: Optional["Player"] = Relationship()
    selling_club: Optional["Club"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[TransferListing.club_id]"})
    current_bidder: Optional["Club"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[TransferListing.current_bidder_id]"})
    triggered_by: Optional["Club"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[TransferListing.triggered_by_club_id]"})
    winning_club: Optional["Club"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[TransferListing.winning_club_id]"})

# ==========================================
# TRANSFER BID MODEL
# ==========================================

class TransferBid(SQLModel, table=True):
    """
    Tracks individual bids placed on transfer listings.
    Maintains complete auction history for transparency.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    transfer_listing_id: int = Field(foreign_key="transferlisting.id")
    bidding_club_id: int = Field(foreign_key="club.id")
    
    # Bid details
    bid_amount: int = Field(description="Amount bid")
    bid_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Bid status
    is_winning: bool = Field(default=False, description="Currently the highest bid")
    was_auto_bid: bool = Field(default=False, description="Generated by auto-bid system")
    
    # Relationships
    transfer_listing: Optional["TransferListing"] = Relationship()
    bidding_club: Optional["Club"] = Relationship()

# ==========================================
# PYDANTIC SCHEMAS FOR API
# ==========================================

# ==========================================
# FREE AGENT SCHEMAS
# ==========================================

class FreeAgentRead(BaseModel):
    """Schema for displaying free agents"""
    player_id: int
    name: str
    age: int
    position: str
    energy: int
    asking_price: int  # Sign-on fee
    days_since_free: int
    
    class Config:
        from_attributes = True

class SignFreeAgentRequest(BaseModel):
    """Schema for signing a free agent"""
    sign_on_fee: int = Field(ge=1, description="Sign-on fee to offer the player")
    daily_wage: int = Field(ge=50, le=1000, description="Daily wage to offer")
    contract_length_days: int = Field(ge=7, le=365, description="Contract length in days")

class SignFreeAgentResponse(BaseModel):
    """Schema for free agent signing response"""
    success: bool
    player_name: str
    sign_on_fee: int
    daily_wage: int
    contract_expires: date
    message: str

class ContractRead(BaseModel):
    """Schema for returning contract information"""
    player_id: int
    club_id: int
    daily_wage: int
    contract_start: date
    contract_expires: date
    days_remaining: int
    preference_type: ContractPreference
    auto_generated: bool
    
    class Config:
        from_attributes = True

class TransferListingRead(BaseModel):
    """Schema for returning transfer listing information"""
    id: int
    player_id: int
    club_id: int
    transfer_type: TransferType
    asking_price: int
    auction_end: datetime
    status: AuctionStatus
    current_bid: int
    current_bidder_id: Optional[int]
    bid_count: int
    minutes_remaining: int
    
    class Config:
        from_attributes = True

class CreateAuctionRequest(BaseModel):
    """Schema for creating a new auction"""
    player_id: int
    starting_price: int
    auction_duration_minutes: int = Field(ge=15, le=1440, description="15 minutes to 24 hours")

class CreateTransferListRequest(BaseModel):
    """Schema for adding player to transfer list"""
    player_id: int
    asking_price: int

class PlaceBidRequest(BaseModel):
    """Schema for placing a bid on a transfer listing"""
    bid_amount: int
    auto_bid_limit: Optional[int] = Field(default=None, description="Maximum amount for auto-bidding")

class TransferBidRead(BaseModel):
    """Schema for returning bid information"""
    id: int
    transfer_listing_id: int
    bidding_club_id: int
    bid_amount: int
    bid_time: datetime
    is_winning: bool
    
    class Config:
        from_attributes = True

# ==========================================
# CONTRACT NEGOTIATION SCHEMAS
# ==========================================

class ContractOfferRequest(BaseModel):
    """Schema for offering a new contract to a player"""
    player_id: int
    daily_wage: int
    contract_length_days: int = Field(ge=1, le=365, description="1 day to 1 year maximum")

class ContractOfferResponse(BaseModel):
    """Schema for player's response to contract offer"""
    accepted: bool
    counter_offer: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None