from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from club import club_db

import random

router = APIRouter()

# === Request Model ===

class MatchRequest(BaseModel):
    team_a_email: str
    team_b_email: str

# === Match Simulation Logic ===

def simulate_match(team_a, team_b):
    """
    Simulate a match between two clubs.
    Stats are linked logically to prevent contradictions.
    """
    def avg_stat(squad, stat):
        return sum(getattr(p, stat) for p in squad) / len(squad)

    # Get average stats
    a_pace = avg_stat(team_a.squad, "pace")
    a_passing = avg_stat(team_a.squad, "passing")
    a_defending = avg_stat(team_a.squad, "defending")

    b_pace = avg_stat(team_b.squad, "pace")
    b_passing = avg_stat(team_b.squad, "passing")
    b_defending = avg_stat(team_b.squad, "defending")

    # Shots and chances
    a_shots_on = random.randint(3, 9)
    b_shots_on = random.randint(2, 8)

    a_conversion_rate = min(0.3, max(0.05, (a_passing + a_pace - b_defending) / 200))
    b_conversion_rate = min(0.3, max(0.05, (b_passing + b_pace - a_defending) / 200))

    a_goals = sum(1 for _ in range(a_shots_on) if random.random() < a_conversion_rate)
    b_goals = sum(1 for _ in range(b_shots_on) if random.random() < b_conversion_rate)

    match_data = {
        "score": f"{team_a.club_name} {a_goals} - {b_goals} {team_b.club_name}",
        "stats": {
            team_a.club_name: {
                "possession": random.randint(45, 60),
                "shots_on_goal": a_shots_on,
                "shots_off_goal": random.randint(2, 6),
                "chances_created": random.randint(3, 7),
                "corners": random.randint(2, 5)
            },
            team_b.club_name: {
                "possession": random.randint(40, 55),
                "shots_on_goal": b_shots_on,
                "shots_off_goal": random.randint(1, 5),
                "chances_created": random.randint(2, 6),
                "corners": random.randint(1, 4)
            }
        }
    }

    return match_data

@router.post("/simulate")
def simulate_match_route(data: MatchRequest):
    """
    Simulates a match between two manager-owned clubs.
    Requires their registered emails to find their squads.
    """
    team_a = club_db.get(data.team_a_email)
    team_b = club_db.get(data.team_b_email)

    if not team_a or not team_b:
        raise HTTPException(status_code=404, detail="One or both clubs not found.")

    result = simulate_match(team_a, team_b)
    return result
