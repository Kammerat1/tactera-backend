from sqlmodel import Session, select
from models import StatLevelRequirement

def calculate_level_from_xp(stat_xp: int, session: Session) -> int:
    """
    Takes total XP for a stat and returns the corresponding level
    based on the statlevelrequirement table.
    """
    statement = (
        select(StatLevelRequirement)
        .where(StatLevelRequirement.xp_required <= stat_xp)
        .order_by(StatLevelRequirement.level.desc())
        .limit(1)
    )
    result = session.exec(statement).first()
    return result.level if result else 1

def add_xp_to_stat(player_id: int, stat_name: str, xp_amount: int, session: Session):
    from models import Player  # Local import to avoid circular issues

    # Load the player
    player = session.get(Player, player_id)
    if not player:
        raise ValueError("Player not found")

    # Determine the XP field name (e.g., 'pace_xp')
    xp_field = f"{stat_name}_xp"

    if not hasattr(player, xp_field):
        raise ValueError(f"Stat '{stat_name}' is invalid")

    # Add XP
    current_xp = getattr(player, xp_field)
    new_xp = current_xp + xp_amount
    setattr(player, xp_field, new_xp)

    # Commit changes
    session.add(player)
    session.commit()

    # Return new level
    return calculate_level_from_xp(new_xp, session)

