from sqlmodel import select, Session
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.injury_model import Injury

async def tick_injuries(db: AsyncSession):
    """
    Decrement injury days_remaining daily and update rehab/fitness.
    """
    result = await db.execute(select(Injury).where(Injury.days_remaining > 0))
    injuries = result.scalars().all()
    tz = timezone(timedelta(hours=2))
    
    result = await db.execute(select(Injury).where(Injury.days_remaining > 0))
    injuries = result.scalars().all()

    if not injuries:
        print(f"[{datetime.now(tz)}] 💤 No injuries to update today.")
        return {
            "updated_injuries": 0,
            "injuries": []
        }


    for injury in injuries:
    # Decrement recovery timer
        injury.days_remaining -= 1

        if injury.days_remaining > 0:
            print(f"[{datetime.now(tz)}] ⏳ Injury Progress: Player {injury.player_id} - "
                f"{injury.name} ({injury.severity}), {injury.days_remaining} days left.")

        # If entering rehab phase
        if injury.days_remaining <= (injury.days_total - injury.rehab_start) and not injury.fit_for_matches:
            injury.fit_for_matches = True
            print(f"[{datetime.now(tz)}] 🏃 Rehab Started: Player {injury.player_id} is now fit enough for matches.")

        # Fully recovered
        if injury.days_remaining <= 0:
            injury.days_remaining = 0
            injury.fit_for_matches = True
            print(f"[{datetime.now(tz)}] ✅ Injury Healed: Player {injury.player_id} fully recovered from {injury.name}.")


        db.add(injury)

    await db.commit()
    
    print(f"[{datetime.now(tz)}] 📊 Daily Injury Tick: {len(injuries)} injuries updated.")

    return {
    "updated_injuries": len(injuries),
    "injuries": [
        {
            "player_id": i.player_id,
            "injury": i.name,
            "severity": i.severity,
            "days_remaining": i.days_remaining,
            "fit_for_matches": i.fit_for_matches
        }
        for i in injuries
    ]
}
# ✅ CHECK IF A PLAYER IS FULLY INJURED
async def is_player_fully_injured(player_id: int, session: AsyncSession) -> bool:
    """
    Returns True if the player currently has an active injury (days_remaining > 0).
    """
    from app.models.injury_model import Injury

    stmt = select(Injury).where(
        Injury.player_id == player_id,
        Injury.days_remaining > 0
    )

    result = await session.execute(stmt)
    injury = result.scalars().first()
    return injury is not None
