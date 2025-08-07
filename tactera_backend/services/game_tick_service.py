from sqlalchemy.ext.asyncio import AsyncSession
from tactera_backend.services.injury_service import tick_injuries
from sqlalchemy.future import select
from tactera_backend.models.player_model import Player
from tactera_backend.services.injury_service import is_player_fully_injured

async def process_daily_tick(db: AsyncSession):
    """
    Advances the game by one day:
    - Decrements injury timers
    (Future: training XP, match scheduling, contracts, etc.)
    """
    # Recover energy for all players
    energy_result = await recover_player_energy(db)

    # Tick down injury days for all injured players
    injury_result = await tick_injuries(db)


    return {
        "message": "Daily tick processed.",
        "energy_result": energy_result,
        "injury_result": injury_result
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

