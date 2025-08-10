from sqlalchemy.ext.asyncio import AsyncSession
from tactera_backend.services.injury_service import tick_injuries
from sqlalchemy.future import select
from tactera_backend.models.player_model import Player
from tactera_backend.services.injury_service import is_player_fully_injured
from tactera_backend.models.contract_model import PlayerContract, TransferListing, TransferType, AuctionStatus

async def process_daily_tick(db: AsyncSession):
    """
    Advances the game by one day:
    - Decrements injury timers
    - Processes expired contracts (creates auctions)
    (Future: training XP, match scheduling, contracts, etc.)
    """
    # Recover energy for all players
    energy_result = await recover_player_energy(db)

    # Tick down injury days for all injured players
    injury_result = await tick_injuries(db)

    # NEW: Process expired contracts
    contract_result = await process_expired_contracts(db)

    return {
        "message": "Daily tick processed.",
        "energy_result": energy_result,
        "injury_result": injury_result,
        "contract_result": contract_result
    }
    
# 🛌 ENERGY RECOVERY SYSTEM
async def recover_player_energy(db: AsyncSession):
    """
    Restores energy to all non-injured players each day.
    - Fully injured players are skipped.
    - Energy is capped at 100.
    """
    from tactera_backend.models.player_model import Player
    from tactera_backend.services.injury_service import is_player_fully_injured

    result = []
    stmt = select(Player)
    result = await db.execute(stmt)
    players = result.scalars().all()


    for player in players:
        if is_player_fully_injured(player.id, db):
            continue  # Skip fully injured players

        old_energy = player.energy
        player.energy = min(100, player.energy + 10)  # Restore 10 energy
        await db.merge(player)
        result.append({
            "player_id": player.id,
            "old_energy": old_energy,
            "new_energy": player.energy,
        })

    await db.commit()
    result = await db.execute(stmt)
    players = result.scalars().all()
    print(f"💤 Energy recovered for {len(players)} players.")

    for player in players:
        print(f"⚡ Player {player.id} now has {player.energy} energy.")

    return {
        "recovered_players": len(players),
        "players": [player.id for player in players]  # Optional: remove this if too noisy
    }

async def process_expired_contracts(db: AsyncSession):
    """
    Find contracts that expired today and create 24-hour auctions for those players.
    Starting price is 1, and proceeds go to the original club.
    """
    from datetime import date, datetime, timedelta
    from tactera_backend.models.contract_model import PlayerContract, TransferListing, TransferType, AuctionStatus
    from tactera_backend.models.player_model import Player
    
    today = date.today()
    
    # Find contracts that expired today
    result = await db.execute(
        select(PlayerContract).where(PlayerContract.contract_expires == today)
    )
    expired_contracts = result.scalars().all()
    
    if not expired_contracts:
        return {
            "expired_contracts": 0,
            "auctions_created": 0,
            "players": []
        }
    
    auctions_created = []
    
    for contract in expired_contracts:
        # Get the player
        player = await db.get(Player, contract.player_id)
        if not player:
            continue
            
        # Check if player is already on the transfer market
        existing_listing = await db.execute(
            select(TransferListing).where(
                TransferListing.player_id == contract.player_id,
                TransferListing.status == AuctionStatus.ACTIVE
            )
        )
        if existing_listing.scalar_one_or_none():
            continue  # Skip if already listed
        
        # Remove player from club control immediately
        original_club_id = contract.club_id
        player.club_id = None  # Player becomes uncontrolled during auction

        # Delete the expired contract
        await db.delete(contract)

        # Create 24-hour auction starting at price 1
        auction_end = datetime.utcnow() + timedelta(hours=24)

        contract_expiry_listing = TransferListing(
            player_id=contract.player_id,
            club_id=original_club_id,  # Original club still gets money if there are bids
            transfer_type=TransferType.AUCTION,
            asking_price=1,  # Starting price of 1
            auction_start=datetime.utcnow(),
            auction_end=auction_end,
            auction_duration_minutes=1440,  # 24 hours = 1440 minutes
            current_bid=0,  # No bids yet
            status=AuctionStatus.ACTIVE
        )

        db.add(player)  # Save the club_id = None change
        
        db.add(contract_expiry_listing)
        
        auctions_created.append({
            "player_id": player.id,
            "player_name": f"{player.first_name} {player.last_name}",
            "original_club_id": contract.club_id,
            "auction_end": auction_end
        })
        
        print(f"Created contract expiry auction for {player.first_name} {player.last_name} (24 hours)")
    
    await db.commit()
    
    return {
        "expired_contracts": len(expired_contracts),
        "auctions_created": len(auctions_created),
        "players": auctions_created
    }