# tactera_backend/seed/seed_formations.py
# Seeds popular football formation templates

from sqlmodel import Session, select
from tactera_backend.core.database import sync_engine
from tactera_backend.models.formation_model import FormationTemplate

def seed_formation_templates():
    """
    Seeds popular football formations with position coordinates.
    Coordinates are percentage-based (0-100) for flexible UI rendering.
    """
    print("⚽ Starting formation template seeding...")

    formations = [
        {
            "name": "4-4-2",
            "description": "Classic balanced formation with two strikers",
            "attacking_mentality": 6,
            "width": 7,
            "positions": {
                # Goalkeeper
                "GK": {"x": 50, "y": 5, "role": "Goalkeeper"},
                
                # Defense (4 players)
                "LB": {"x": 15, "y": 20, "role": "Left Back"},
                "CB1": {"x": 35, "y": 20, "role": "Centre Back"},
                "CB2": {"x": 65, "y": 20, "role": "Centre Back"},
                "RB": {"x": 85, "y": 20, "role": "Right Back"},
                
                # Midfield (4 players)
                "LM": {"x": 15, "y": 50, "role": "Left Midfielder"},
                "CM1": {"x": 35, "y": 50, "role": "Central Midfielder"},
                "CM2": {"x": 65, "y": 50, "role": "Central Midfielder"},
                "RM": {"x": 85, "y": 50, "role": "Right Midfielder"},
                
                # Attack (2 players)
                "ST1": {"x": 40, "y": 80, "role": "Striker"},
                "ST2": {"x": 60, "y": 80, "role": "Striker"}
            }
        },
        {
            "name": "4-3-3",
            "description": "Attacking formation with wingers and one striker",
            "attacking_mentality": 8,
            "width": 8,
            "positions": {
                # Goalkeeper
                "GK": {"x": 50, "y": 5, "role": "Goalkeeper"},
                
                # Defense (4 players)
                "LB": {"x": 15, "y": 20, "role": "Left Back"},
                "CB1": {"x": 35, "y": 20, "role": "Centre Back"},
                "CB2": {"x": 65, "y": 20, "role": "Centre Back"},
                "RB": {"x": 85, "y": 20, "role": "Right Back"},
                
                # Midfield (3 players)
                "CDM": {"x": 50, "y": 40, "role": "Defensive Midfielder"},
                "CM1": {"x": 35, "y": 55, "role": "Central Midfielder"},
                "CM2": {"x": 65, "y": 55, "role": "Central Midfielder"},
                
                # Attack (3 players)
                "LW": {"x": 20, "y": 80, "role": "Left Winger"},
                "ST": {"x": 50, "y": 85, "role": "Striker"},
                "RW": {"x": 80, "y": 80, "role": "Right Winger"}
            }
        },
        {
            "name": "3-5-2",
            "description": "Three at the back with wing-backs",
            "attacking_mentality": 7,
            "width": 9,
            "positions": {
                # Goalkeeper
                "GK": {"x": 50, "y": 5, "role": "Goalkeeper"},
                
                # Defense (3 players)
                "CB1": {"x": 25, "y": 20, "role": "Centre Back"},
                "CB2": {"x": 50, "y": 20, "role": "Centre Back"},
                "CB3": {"x": 75, "y": 20, "role": "Centre Back"},
                
                # Midfield (5 players)
                "LWB": {"x": 10, "y": 45, "role": "Left Wing-Back"},
                "CM1": {"x": 35, "y": 50, "role": "Central Midfielder"},
                "CM2": {"x": 50, "y": 45, "role": "Central Midfielder"},
                "CM3": {"x": 65, "y": 50, "role": "Central Midfielder"},
                "RWB": {"x": 90, "y": 45, "role": "Right Wing-Back"},
                
                # Attack (2 players)
                "ST1": {"x": 40, "y": 80, "role": "Striker"},
                "ST2": {"x": 60, "y": 80, "role": "Striker"}
            }
        },
        {
            "name": "5-3-2",
            "description": "Defensive formation with five at the back",
            "attacking_mentality": 4,
            "width": 6,
            "positions": {
                # Goalkeeper
                "GK": {"x": 50, "y": 5, "role": "Goalkeeper"},
                
                # Defense (5 players)
                "LWB": {"x": 10, "y": 25, "role": "Left Wing-Back"},
                "CB1": {"x": 30, "y": 20, "role": "Centre Back"},
                "CB2": {"x": 50, "y": 20, "role": "Centre Back"},
                "CB3": {"x": 70, "y": 20, "role": "Centre Back"},
                "RWB": {"x": 90, "y": 25, "role": "Right Wing-Back"},
                
                # Midfield (3 players)
                "CM1": {"x": 35, "y": 50, "role": "Central Midfielder"},
                "CM2": {"x": 50, "y": 45, "role": "Central Midfielder"},
                "CM3": {"x": 65, "y": 50, "role": "Central Midfielder"},
                
                # Attack (2 players)
                "ST1": {"x": 40, "y": 75, "role": "Striker"},
                "ST2": {"x": 60, "y": 75, "role": "Striker"}
            }
        },
        {
            "name": "4-2-3-1",
            "description": "Modern formation with attacking midfielder",
            "attacking_mentality": 7,
            "width": 7,
            "positions": {
                # Goalkeeper
                "GK": {"x": 50, "y": 5, "role": "Goalkeeper"},
                
                # Defense (4 players)
                "LB": {"x": 15, "y": 20, "role": "Left Back"},
                "CB1": {"x": 35, "y": 20, "role": "Centre Back"},
                "CB2": {"x": 65, "y": 20, "role": "Centre Back"},
                "RB": {"x": 85, "y": 20, "role": "Right Back"},
                
                # Defensive Midfield (2 players)
                "CDM1": {"x": 40, "y": 40, "role": "Defensive Midfielder"},
                "CDM2": {"x": 60, "y": 40, "role": "Defensive Midfielder"},
                
                # Attacking Midfield (3 players)
                "LM": {"x": 20, "y": 60, "role": "Left Midfielder"},
                "CAM": {"x": 50, "y": 65, "role": "Attacking Midfielder"},
                "RM": {"x": 80, "y": 60, "role": "Right Midfielder"},
                
                # Attack (1 player)
                "ST": {"x": 50, "y": 85, "role": "Striker"}
            }
        }
    ]

    with Session(sync_engine) as session:
        for formation_data in formations:
            # Check if formation already exists
            existing = session.exec(
                select(FormationTemplate).where(FormationTemplate.name == formation_data["name"])
            ).first()
            
            if existing:
                print(f"   ✅ Formation already exists: {formation_data['name']}")
                continue
            
            # Create new formation template
            formation = FormationTemplate(**formation_data)
            session.add(formation)
            print(f"   ➕ Added formation: {formation_data['name']}")
        
        session.commit()
    
    print("✅ Formation template seeding complete!")


if __name__ == "__main__":
    seed_formation_templates()