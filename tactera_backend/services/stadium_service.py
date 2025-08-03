from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tactera_backend.models.stadium_model import Stadium, StadiumPart
from tactera_backend.core.stadium_config import LEVEL_TO_PITCH, LEVEL_TO_CAPACITY

async def recalculate_stadium_attributes(session: AsyncSession, stadium_id: int):
    """
    Recalculate pitch_quality and capacity for a stadium
    based on the current levels of its StadiumParts.
    """
    stadium = await session.get(Stadium, stadium_id)
    if not stadium:
        raise ValueError(f"Stadium {stadium_id} not found.")

    # Fetch stadium parts
    result = await session.execute(select(StadiumPart).where(StadiumPart.stadium_id == stadium_id))
    parts = result.scalars().all()

    # Extract pitch and stands
    pitch = next((p for p in parts if p.type == "pitch"), None)
    stands = [p for p in parts if "stand" in p.type]

    # Recalculate pitch quality
    if pitch:
        stadium.pitch_quality = LEVEL_TO_PITCH.get(pitch.level, stadium.pitch_quality)

    # Recalculate capacity (average stand levels)
    if stands:
        avg_stand_level = round(sum(p.level for p in stands) / len(stands))
        stadium.capacity = LEVEL_TO_CAPACITY.get(avg_stand_level, stadium.capacity)

    session.add(stadium)
    await session.commit()
    print(f"🔄 Stadium {stadium.name} updated: Capacity={stadium.capacity}, Pitch={stadium.pitch_quality}")


async def upgrade_stadium_part(session: AsyncSession, part_id: int) -> StadiumPart:
    part = await session.get(StadiumPart, part_id)
    if not part:
        raise ValueError(f"StadiumPart {part_id} not found.")

    if part.level < 5:
        part.level += 1
        session.add(part)
        await session.commit()
        await recalculate_stadium_attributes(session, part.stadium_id)
        return part
    else:
        raise ValueError(f"{part.type} is already at max level.")
