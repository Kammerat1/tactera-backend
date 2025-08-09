from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tactera_backend.core.database import get_db
from tactera_backend.models.player_model import Player

router = APIRouter()

@router.get("/debug/players")
async def debug_list_players(db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint: List all players with their first/last name and club ID.
    """
    result = await db.execute(select(Player))
    players = result.scalars().all()
    return [
        {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "club_id": p.club_id
        }
        for p in players
    ]

from typing import Literal, Optional
from fastapi import Body, HTTPException
from sqlmodel import select
from tactera_backend.models.club_model import Club
from tactera_backend.core.training_intensity import ALLOWED_INTENSITIES

@router.get("/debug/club/{club_id}/training-intensity")
async def get_club_training_intensity(club_id: int, db: AsyncSession = Depends(get_db)):
    """Return the club's current training intensity setting."""
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return {"club_id": club_id, "training_intensity": club.training_intensity}

@router.post("/debug/club/{club_id}/training-intensity")
async def set_club_training_intensity(
    club_id: int,
    intensity: Literal["light", "normal", "hard"] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the club's training intensity.
    Hybrid rule (future): 'hard' requires physio dept >= 1.
    For now, we allow all three and will enforce when physio exists.
    """
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    intensity = intensity.lower()
    if intensity not in ALLOWED_INTENSITIES:
        raise HTTPException(status_code=400, detail=f"Invalid intensity. Allowed: {sorted(ALLOWED_INTENSITIES)}")

    # TODO (future): enforce 'hard' lock behind physio department >= 1
    club.training_intensity = intensity
    db.add(club)
    await db.commit()
    await db.refresh(club)

    return {
        "club_id": club_id,
        "training_intensity": club.training_intensity,
        "note": "Hard will be locked behind physio later.",
    }

# ==============================================
# 🧪 DEBUG: Force reinjury test states (temporary)
# Creates three controlled player states so the match simulator
# shows reinjury multipliers in one run:
# 1) One player in active rehab (days_remaining > 0 and <= rehab_start)
# 2) One player recently healed (healed within window)
# 3) One player with very low energy (e.g., 10)
# ----------------------------------------------
# IMPORTANT: Remove this route after testing.
# ==============================================
from datetime import datetime, timedelta
from fastapi import Body
from sqlmodel import select
from tactera_backend.core.database import get_session
from tactera_backend.models.player_model import Player
from tactera_backend.models.injury_model import Injury
from tactera_backend.core.injury_config import RECENT_HEALED_WINDOW_DAYS

@router.post("/debug/force-reinjury-test")
def debug_force_reinjury_test(
    club_id: int = Body(..., embed=True),
    session = Depends(get_session),
):
    """
    Tell me to...
    Force three players into known states so the reinjury multipliers can be seen:
    - Player A: Active rehab
    - Player B: Recently healed
    - Player C: Low energy
    """
    # --- fetch 3 players from this club ---
    players = session.exec(
        select(Player).where(Player.club_id == club_id).order_by(Player.id)
    ).all()

    if len(players) < 3:
        return {"ok": False, "error": "Club needs at least 3 players for this test."}

    p_rehab = players[0]
    p_recent = players[1]
    p_low = players[2]

    # --- clear existing active injuries for clarity (optional but tidy) ---
    active_injs = session.exec(
        select(Injury).where(Injury.player_id.in_([p_rehab.id, p_recent.id]))
    ).all()
    for inj in active_injs:
        # If any injury is still active, mark as fully healed to avoid confusion
        if inj.days_remaining and inj.days_remaining > 0:
            inj.days_remaining = 0
            inj.fit_for_matches = True
    session.commit()

    now = datetime.utcnow()

    # 1) Force ACTIVE REHAB on p_rehab:
    #    days_total=7, rehab_start=3 -> consider rehab when days_remaining <= 3
    #    we set days_remaining=2 to be inside rehab
    rehab_injury = Injury(
        player_id=p_rehab.id,
        name="Test Rehab Strain",
        type="muscle",
        severity="moderate",
        start_date=now - timedelta(days=5),   # started 5 days ago
        days_total=7,                         # total duration
        rehab_start=3,                        # rehab starts in last 3 days
        rehab_xp_multiplier=0.5,              # not relevant for match sim, fine for debug
        fit_for_matches=False,
        days_remaining=2,                     # <= rehab_start (in rehab window)
    )
    session.add(rehab_injury)

    # 2) Force RECENTLY HEALED on p_recent:
    #    healed = start_date + days_total
    #    Make healed happen within RECENT_HEALED_WINDOW_DAYS
    days_total_recent = 5
    days_since_healed = min(RECENT_HEALED_WINDOW_DAYS, 3)  # healed 3 days ago
    recent_start = now - timedelta(days=(days_total_recent + days_since_healed))
    recent_injury = Injury(
        player_id=p_recent.id,
        name="Test Recent Knock",
        type="impact",
        severity="minor",
        start_date=recent_start,
        days_total=days_total_recent,
        rehab_start=1,
        rehab_xp_multiplier=0.8,
        fit_for_matches=True,
        days_remaining=0,  # healed
    )
    session.add(recent_injury)

    # 3) Force LOW ENERGY on p_low:
    p_low.energy = 10  # well below typical threshold (e.g., 50)

    session.commit()

    return {
        "ok": True,
        "club_id": club_id,
        "players": {
            "rehab": {"id": p_rehab.id, "name": f"{p_rehab.first_name} {p_rehab.last_name}"},
            "recent": {"id": p_recent.id, "name": f"{p_recent.first_name} {p_recent.last_name}"},
            "low_energy": {"id": p_low.id, "name": f"{p_low.first_name} {p_low.last_name}", "energy": p_low.energy},
        },
        "note": "Run /simulate with this club in a match. Check injury_risk_debug for multipliers and reasons.",
    }
