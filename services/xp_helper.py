from sqlmodel import Session, select
from tactera_backend.models.stat_level_requirement import StatLevelRequirement
from tactera_backend.models.player import Player

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
    from tactera_backend.models.player import Player  # Local import to avoid circular issues

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

def add_xp_to_stat(player_id: int, stat_name: str, xp_amount: int, session):
    """
    Adds XP to a player's stat (e.g., 'pace', 'passing') by updating the corresponding *_xp field.

    Parameters:
    - player_id: ID of the player we want to update
    - stat_name: Name of the stat (like 'pace', 'passing', etc.)
    - xp_amount: How much XP to add
    - session: Database session (passed in from the route)
    """

    # Map stat names to the actual column names in the database
    stat_field_name = f"{stat_name}_xp"  # e.g., 'pace' → 'pace_xp'

    # Get the player from the database
    player = session.get(Player, player_id)

    # If the player doesn't exist, return an error
    if not player:
        raise ValueError(f"Player with ID {player_id} not found.")

    # Check if the player actually has this stat field (like 'pace_xp')
    if not hasattr(player, stat_field_name):
        raise ValueError(f"Stat '{stat_name}' is not valid.")

    # Get the current XP value for the stat
    current_xp = getattr(player, stat_field_name)

    # Add the new XP amount
    new_xp = current_xp + xp_amount

    # Update the stat XP on the player
    setattr(player, stat_field_name, new_xp)

    # Save the change to the database
    session.commit()
