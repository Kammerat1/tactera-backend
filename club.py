from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random

router = APIRouter()

# Temporary in-memory "database" for clubs
club_db = {}

# === Models ===

# A single player in the squad
class Player(BaseModel):
    name: str
    position: str
    pace: int
    passing: int
    defending: int

# A club owned by a manager
class Club(BaseModel):
    manager_email: str
    club_name: str
    squad: list[Player]

# === Helper Data ===

POSITIONS = ["GK", "LB", "CB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]
NAMES = ["Renzo", "Silas", "Toma", "Lior", "Marek", "Niko", "Otto", "Sami", "Jari", "Eryk", "Kai", "Levi", "Rafi"]

# === Squad Generator Function ===

def generate_squad() -> list[Player]:
    """Creates a list of 11 fictional players with random stats and positions."""
    squad = []
    used_names = set()

    for i in range(11):
        name = random.choice(NAMES)
        while name in used_names:
            name = random.choice(NAMES)
        used_names.add(name)

        position = POSITIONS[i % len(POSITIONS)]
        pace = random.randint(40, 95)
        passing = random.randint(40, 95)
        defending = random.randint(40, 95)

        player = Player(
            name=name,
            position=position,
            pace=pace,
            passing=passing,
            defending=defending
        )
        squad.append(player)
    
    return squad

# === Routes ===

@router.post("/create")
def create_club(manager_email: str, club_name: str):
    """
    Creates a club and assigns it to a manager.
    Generates a squad of 11 fictional players.
    """
    if manager_email in club_db:
        raise HTTPException(status_code=400, detail="Club already exists for this manager.")

    squad = generate_squad()
    new_club = Club(manager_email=manager_email, club_name=club_name, squad=squad)
    club_db[manager_email] = new_club
    return {"message": f"Club '{club_name}' created successfully", "squad": squad}

@router.get("/{manager_email}")
def get_club(manager_email: str):
    """
    Retrieves the club and squad for a given manager by email.
    """
    club = club_db.get(manager_email)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")
    return club

# === PRELOAD TEST CLUBS ===

def preload_test_clubs():
    """
    Generates two always-available test clubs for dev use.
    """
    if "test1@tactera.dev" not in club_db:
        squad_a = generate_squad()
        club_db["test1@test.dk"] = Club(
            manager_email="test1@tactera.dev",
            club_name="Tactera United",
            squad=squad_a
        )
    
    if "test2@tactera.dev" not in club_db:
        squad_b = generate_squad()
        club_db["test2@test.dk"] = Club(
            manager_email="test2@tactera.dev",
            club_name="FC Dev Mode",
            squad=squad_b
        )

# Call this function when club.py is imported
preload_test_clubs()
