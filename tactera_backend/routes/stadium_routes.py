# tactera_backend/routes/stadium_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.core.database import get_db, sync_engine, Session
from tactera_backend.models.stadium_model import Stadium, StadiumPart
from tactera_backend.services.stadium_service import upgrade_stadium_part
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/parts/{part_id}/upgrade")
@router.post("/parts/{part_id}/upgrade")
async def upgrade_part(part_id: int, db: AsyncSession = Depends(get_db)):
    """
    Upgrade a stadium part (pitch or stands) and recalculate stadium attributes.
    """
    try:
        updated_part = await upgrade_stadium_part(db, part_id)  # ✅ Returns upgraded part
        return {"message": f"{updated_part.type} upgraded to Level {updated_part.level} successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{stadium_id}")
def get_stadium(stadium_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a stadium's details, including parts, capacity, and pitch quality.
    """
    stadium = db.get(Stadium, stadium_id)
    if not stadium:
        raise HTTPException(status_code=404, detail=f"Stadium {stadium_id} not found.")

    # Fetch all stadium parts linked to this stadium
    parts = db.exec(select(StadiumPart).where(StadiumPart.stadium_id == stadium_id)).all()

    return {
        "id": stadium.id,
        "name": stadium.name,
        "sponsor_name": stadium.sponsor_name,
        "club_id": stadium.club_id,
        "capacity": stadium.capacity,
        "pitch_quality": stadium.pitch_quality,
        "base_ticket_price": stadium.base_ticket_price,
        "parts": [
            {
                "id": part.id,
                "type": part.type,
                "level": part.level,
                "durability": part.durability,
            }
            for part in parts
        ],
    }
    
@router.get("/club/{club_id}")
async def get_stadium_by_club(club_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a stadium linked to a specific club, including its parts.
    """
    result = await db.execute(select(Stadium).where(Stadium.club_id == club_id))
    stadium = result.scalar_one_or_none()
    if not stadium:
        raise HTTPException(status_code=404, detail=f"No stadium found for club {club_id}")

    parts_result = await db.execute(select(StadiumPart).where(StadiumPart.stadium_id == stadium.id))
    parts = parts_result.scalars().all()

    return {
        "id": stadium.id,
        "name": stadium.name,
        "sponsor_name": stadium.sponsor_name,
        "club_id": stadium.club_id,
        "capacity": stadium.capacity,
        "pitch_quality": stadium.pitch_quality,
        "base_ticket_price": stadium.base_ticket_price,
        "parts": [
            {
                "id": part.id,
                "type": part.type,
                "level": part.level,
                "durability": part.durability,
            }
            for part in parts
        ],
    }

@router.post("/{stadium_id}/upgrade_all_stands")
async def upgrade_all_stands(stadium_id: int, db: AsyncSession = Depends(get_db)):
    """
    Upgrade all stands of a stadium by 1 level each (if not already maxed).
    Automatically recalculates stadium capacity.
    """
    # Fetch all stands for this stadium
    result = await db.execute(
        select(StadiumPart).where(
            StadiumPart.stadium_id == stadium_id, StadiumPart.type.like("stand_%")
        )
    )
    stands = result.scalars().all()

    if not stands:
        raise HTTPException(status_code=404, detail=f"No stands found for stadium {stadium_id}")

    upgraded = []
    for stand in stands:
        if stand.level < 5:
            stand.level += 1
            db.add(stand)
            upgraded.append(f"{stand.type} upgraded to Level {stand.level}")
        else:
            upgraded.append(f"{stand.type} already at max level")

    await db.commit()

    # Recalculate stadium attributes
    from tactera_backend.services.stadium_service import recalculate_stadium_attributes
    await recalculate_stadium_attributes(db, stadium_id)

    return {
        "message": "Stand upgrades processed",
        "details": upgraded
    }

@router.post("/{stadium_id}/upgrade_pitch")
async def upgrade_pitch(stadium_id: int, db: AsyncSession = Depends(get_db)):
    """
    Upgrade the pitch of a stadium by 1 level (if not already maxed).
    Automatically recalculates pitch quality.
    """
    # Fetch the pitch part for this stadium
    result = await db.execute(
        select(StadiumPart).where(
            StadiumPart.stadium_id == stadium_id, StadiumPart.type == "pitch"
        )
    )
    pitch = result.scalars().first()

    if not pitch:
        raise HTTPException(status_code=404, detail=f"No pitch found for stadium {stadium_id}")

    if pitch.level < 5:
        pitch.level += 1
        db.add(pitch)
        await db.commit()

        # Recalculate stadium attributes (pitch quality)
        from tactera_backend.services.stadium_service import recalculate_stadium_attributes
        await recalculate_stadium_attributes(db, stadium_id)

        return {"message": f"Pitch upgraded to Level {pitch.level}"}
    else:
        return {"message": "Pitch is already at max level"}

@router.post("/{stadium_id}/upgrade_all")
async def upgrade_all(stadium_id: int, db: AsyncSession = Depends(get_db)):
    """
    Upgrade all stands and the pitch of a stadium by 1 level each (if not already maxed).
    Automatically recalculates stadium capacity and pitch quality.
    """
    # Fetch all stadium parts (stands + pitch)
    result = await db.execute(
        select(StadiumPart).where(StadiumPart.stadium_id == stadium_id)
    )
    parts = result.scalars().all()

    if not parts:
        raise HTTPException(status_code=404, detail=f"No parts found for stadium {stadium_id}")

    upgraded = []
    for part in parts:
        if part.level < 5:
            part.level += 1
            db.add(part)
            upgraded.append(f"{part.type} upgraded to Level {part.level}")
        else:
            upgraded.append(f"{part.type} already at max level")

    await db.commit()

    # Recalculate stadium attributes (capacity + pitch quality)
    from tactera_backend.services.stadium_service import recalculate_stadium_attributes
    await recalculate_stadium_attributes(db, stadium_id)

    return {
        "message": "All stadium upgrades processed",
        "details": upgraded
    }

@router.post("/debug/parts/{part_id}/set_level")
async def debug_set_part_level(part_id: int, level: int, db: AsyncSession = Depends(get_db)):
    """
    ⚠️ DEBUG ONLY: Directly set a stadium part's level (bypasses upgrade limits).
    Useful for testing and debugging.
    """
    # Validate level
    if level < 1 or level > 5:
        raise HTTPException(status_code=400, detail="Level must be between 1 and 5.")

    # Fetch the part
    part = await db.get(StadiumPart, part_id)
    if not part:
        raise HTTPException(status_code=404, detail=f"StadiumPart {part_id} not found.")

    # Set the level directly
    part.level = level
    db.add(part)
    await db.commit()

    # Recalculate linked stadium attributes
    from tactera_backend.services.stadium_service import recalculate_stadium_attributes
    await recalculate_stadium_attributes(db, part.stadium_id)

    return {
        "message": f"DEBUG: {part.type} forcibly set to Level {level}",
        "stadium_id": part.stadium_id
    }

@router.post("/debug/{stadium_id}/reset")
async def debug_reset_stadium(stadium_id: int, db: AsyncSession = Depends(get_db)):
    """
    ⚠️ DEBUG ONLY: Reset all stadium parts (stands + pitch) to Level 1.
    Automatically recalculates capacity and pitch quality.
    """
    # Fetch all stadium parts
    result = await db.execute(
        select(StadiumPart).where(StadiumPart.stadium_id == stadium_id)
    )
    parts = result.scalars().all()

    if not parts:
        raise HTTPException(status_code=404, detail=f"No parts found for stadium {stadium_id}")

    reset_list = []
    for part in parts:
        part.level = 1
        db.add(part)
        reset_list.append(f"{part.type} reset to Level 1")

    await db.commit()

    # Recalculate stadium attributes
    from tactera_backend.services.stadium_service import recalculate_stadium_attributes
    await recalculate_stadium_attributes(db, stadium_id)

    return {
        "message": "DEBUG: Stadium fully reset to Level 1",
        "details": reset_list
    }

@router.get("/club/{club_id}/match-revenue")
async def calculate_stadium_match_revenue(
    club_id: int, 
    attendance_percentage: float = 0.8,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate potential match revenue for a club's stadium.
    Useful for testing and showing revenue projections.
    """
    from tactera_backend.services.finance_service import calculate_match_revenue
    from tactera_backend.core.database import get_session
    
    # Use sync session for finance service
    with Session(sync_engine) as session:
        revenue_info = calculate_match_revenue(
            session=session,
            home_club_id=club_id,
            attendance_percentage=attendance_percentage
        )
    
    if not revenue_info["success"]:
        raise HTTPException(status_code=404, detail=revenue_info["message"])
    
    # Get current club money for context
    club = await db.get(Club, club_id)
    
    return {
        "club_id": club_id,
        "club_name": club.name if club else "Unknown",
        "current_money": club.money if club else 0,
        "stadium_revenue_projection": revenue_info,
        "revenue_scenarios": {
            "poor_attendance_50%": int(revenue_info["capacity"] * 0.5 * revenue_info["ticket_price"]),
            "average_attendance_75%": int(revenue_info["capacity"] * 0.75 * revenue_info["ticket_price"]),
            "excellent_attendance_95%": int(revenue_info["capacity"] * 0.95 * revenue_info["ticket_price"]),
            "sold_out_100%": int(revenue_info["capacity"] * 1.0 * revenue_info["ticket_price"])
        }
    }