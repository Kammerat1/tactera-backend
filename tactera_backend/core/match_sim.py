# tactera_backend/core/match_sim.py

import random
from typing import Set, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from tactera_backend.models.match_model import Match
from tactera_backend.models.player_model import Player
from tactera_backend.models.club_model import Club
from tactera_backend.models.stadium_model import Stadium
from tactera_backend.models.injury_model import Injury
from tactera_backend.core.injury_generator import calculate_injury_risk, generate_injury
from tactera_backend.core.injury_config import REINJURY_MULTIPLIER
from tactera_backend.core.config import TEST_MODE  # ✅ Ensure TEST_MODE is imported
from tactera_backend.models.suspension_model import Suspension
from tactera_backend.models.formation_model import ClubFormation, FormationTemplate

# =========================================
# 🟨🟥 Booking & Suspension Configuration
# =========================================
# You can tweak these to adjust how often cards happen.
# All values are per-team, per-match "guidelines" used by the generator.

# Approximate target ranges per team
YELLOW_CARDS_MIN = 0
YELLOW_CARDS_MAX = 4

# Probability a team also gets a direct red (independent of yellows)
DIRECT_RED_PROB = 0.10   # 10%

# Direct red suspension length (randomized between these)
RED_SUSPENSION_MIN = 1   # at least 1 match
RED_SUSPENSION_MAX = 3   # up to 3 matches

# Accumulation rule: two yellows in the SAME match = 1 match suspension
TWO_YELLOWS_SUSPENSION = 1


# ----------------------------------------------------
# Helper: randomly generate bookings for a team squad
# ----------------------------------------------------
def generate_team_bookings(player_ids: list[int]) -> dict:
    """
    Returns a dict with per-player bookings for one team:
    {
      "yellow_counts": {player_id: n_yellows_this_match, ...},
      "direct_reds": [player_id, ...]
    }
    """
    if not player_ids:
        return {"yellow_counts": {}, "direct_reds": []}

    # How many yellows shall we give this team?
    num_yellows = random.randint(YELLOW_CARDS_MIN, YELLOW_CARDS_MAX)

    yellow_counts = {}
    for _ in range(num_yellows):
        pid = random.choice(player_ids)
        yellow_counts[pid] = yellow_counts.get(pid, 0) + 1

    # Maybe a direct red (independent of the yellows)
    direct_reds = []
    if random.random() < DIRECT_RED_PROB:
        pid = random.choice(player_ids)
        direct_reds.append(pid)

    return {"yellow_counts": yellow_counts, "direct_reds": direct_reds}


# ---------------------------------------------------------
# Helper: assemble a bookings payload for API visibility
# ---------------------------------------------------------
def build_bookings_payload(home_data: dict, away_data: dict) -> dict:
    """
    Converts the internal booking dicts into a UI-friendly structure:
    {
      "home": [{"player_id": 1, "type": "yellow"}, ...],
      "away": [{"player_id": 9, "type": "red"}, {"player_id": 5, "type": "second_yellow_red"}]
    }
    """
    def expand(side_dict):
        events = []
        # Yellows
        for pid, cnt in side_dict["yellow_counts"].items():
            for _ in range(min(cnt, 2)):  # list each yellow separately (cap at 2 for readability)
                events.append({"player_id": pid, "type": "yellow"})
            if cnt >= 2:
                events.append({"player_id": pid, "type": "second_yellow_red"})
        # Direct reds
        for pid in side_dict["direct_reds"]:
            events.append({"player_id": pid, "type": "red"})
        return events

    return {
        "home": expand(home_data),
        "away": expand(away_data),
    }

async def get_club_match_squad(db: AsyncSession, club_id: int, match_id: int = None) -> dict:
    """
    Get a club's match squad (7-23 players) and starting XI (7-11 players).
    Falls back to auto-selection if no manual selection exists.
    """
    # Get all available players (exclude fully injured)
    result = await db.execute(
        select(Player).where(
            Player.club_id == club_id,
            ~Player.id.in_(select(Injury.player_id).where(Injury.days_remaining > 0))
        )
    )
    available_players = result.scalars().all()
    
    # Check if we have enough players for minimum match squad
    if len(available_players) < 7:
        return {
            "can_play": False,
            "reason": "Insufficient players (need minimum 7)",
            "available_count": len(available_players),
            "match_squad": [],
            "starting_xi": []
        }
    
    # For now, auto-select match squad (we'll add manual selection later)
    # Take up to 18 players for match squad (realistic for most clubs)
    match_squad_size = min(18, len(available_players))
    match_squad = available_players[:match_squad_size]
    
    # Select starting XI from match squad (7-11 players)
    # Priority: use formation if available, otherwise auto-select
    result = await db.execute(
        select(ClubFormation).where(
            ClubFormation.club_id == club_id,
            ClubFormation.is_active == True
        )
    )
    club_formation = result.scalar_one_or_none()
    
    if club_formation and club_formation.player_assignments:
        # Use formation assignments for starting XI
        assigned_player_ids = list(club_formation.player_assignments.values())
        match_squad_ids = {p.id for p in match_squad}
        
        # Filter assigned players to only those in the match squad and available
        valid_assignments = [pid for pid in assigned_player_ids if pid in match_squad_ids]
        
        # ✅ FLEXIBLE STARTING XI: Use what's assigned (7-11 players)
        if len(valid_assignments) >= 7:
            # Have enough assigned players - use them (even if less than 11)
            starting_xi_ids = valid_assignments[:11]  # Cap at 11 maximum
            starting_xi = [p for p in match_squad if p.id in starting_xi_ids]
            formation_info = {
                "has_formation": True,
                "formation_name": "Formation Set",
                "assigned_count": len(starting_xi),
                "auto_filled": 0
            }
        else:
            # Not enough assigned players - fill up to reach minimum 7
            unassigned = [p for p in match_squad if p.id not in valid_assignments]
            needed = max(7, len(valid_assignments)) - len(valid_assignments)
            
            starting_xi_ids = valid_assignments + [p.id for p in unassigned[:needed]]
            starting_xi = [p for p in match_squad if p.id in starting_xi_ids]
            formation_info = {
                "has_formation": True,
                "formation_name": "Formation Set (Auto-filled)",
                "assigned_count": len(valid_assignments),
                "auto_filled": len(starting_xi) - len(valid_assignments)
            }
    else:
        # No formation: auto-select optimal number (prefer 11, minimum 7)
        optimal_starting = min(11, len(match_squad))
        starting_xi = match_squad[:optimal_starting]
        formation_info = {
            "has_formation": False,
            "formation_name": "Auto-Selected",
            "assigned_count": 0,
            "auto_filled": len(starting_xi)
        }
    
    return {
        "can_play": True,
        "reason": "",
        "available_count": len(available_players),
        "match_squad": match_squad,
        "match_squad_size": len(match_squad),
        "starting_xi": starting_xi,
        "starting_xi_count": len(starting_xi),  # ✅ Can be 7-11
        "formation_info": formation_info
    }
    
def validate_formation_for_match(lineup: dict) -> dict:
    """
    Validate that a formation has the minimum required players for a match.
    Returns validation status and any issues.
    """
    if not lineup["has_formation"]:
        return {
            "is_valid": False,
            "issues": ["No formation set"],
            "can_play": False
        }
    
    selected_players = lineup["selected_players"]
    
    if len(selected_players) < 11:
        return {
            "is_valid": False,
            "issues": [f"Only {len(selected_players)} players assigned, need 11"],
            "can_play": len(selected_players) >= 7  # Minimum to play a match
        }
    
    # Check for goalkeeper
    has_goalkeeper = any(p["position"] == "GK" for p in selected_players)
    if not has_goalkeeper:
        return {
            "is_valid": False,
            "issues": ["No goalkeeper assigned"],
            "can_play": False
        }
    
    return {
        "is_valid": True,
        "issues": [],
        "can_play": True
    }

async def simulate_match(db: AsyncSession, fixture_id: int):
    """
    Simulates a single match with proper send-off timing and suspension logic:
    - Players getting cards are immediately removed from the match
    - Suspensions are created AFTER the match ends
    - Suspension countdown doesn't affect the current match
    - Fully injured players are excluded from selection
    - Rehab-phase players can play but face increased reinjury risk
    """

    # 1️⃣ Fetch fixture
    result = await db.execute(select(Match).where(Match.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise ValueError(f"Fixture with ID {fixture_id} not found.")

    # 2️⃣ Fetch clubs
    home_club = await db.get(Club, fixture.home_club_id)
    away_club = await db.get(Club, fixture.away_club_id)

    # 3️⃣ Fetch match squads and starting XIs
    home_squad_info = await get_club_match_squad(db, fixture.home_club_id, fixture.id)
    away_squad_info = await get_club_match_squad(db, fixture.away_club_id, fixture.id)
    
    # Check if both teams can field minimum squads
    if not home_squad_info["can_play"]:
        # Home team can't play - away team wins 3-0
        fixture.home_goals = 0
        fixture.away_goals = 3
        fixture.is_played = True
        fixture.match_time = datetime.utcnow()
        await db.commit()
        
        return {
            "fixture_id": fixture.id,
            "match_abandoned": True,
            "reason": f"Home team: {home_squad_info['reason']}",
            "final_score": "0-3 (Walkover)",
            "home_goals": 0,
            "away_goals": 3,
            "injuries": [],
            "bookings": [],
            "send_offs": []
        }
    
    if not away_squad_info["can_play"]:
        # Away team can't play - home team wins 3-0
        fixture.home_goals = 3
        fixture.away_goals = 0
        fixture.is_played = True
        fixture.match_time = datetime.utcnow()
        await db.commit()
        
        return {
            "fixture_id": fixture.id,
            "match_abandoned": True,
            "reason": f"Away team: {away_squad_info['reason']}",
            "final_score": "3-0 (Walkover)",
            "home_goals": 3,
            "away_goals": 0,
            "injuries": [],
            "bookings": [],
            "send_offs": []
        }
    
    # Both teams can play - get starting XIs
    home_players = home_squad_info["starting_xi"]  # Exactly 11 players
    away_players = away_squad_info["starting_xi"]  # Exactly 11 players
    
    if TEST_MODE:
        print(f"\n🏁 Starting match simulation: {home_club.name} vs {away_club.name}")
        print(f"   Home: {len(home_players)} starting players (squad: {home_squad_info['match_squad_size']})")
        print(f"   Away: {len(away_players)} starting players (squad: {away_squad_info['match_squad_size']})")
        
        # Show if teams are playing with less than 11
        if len(home_players) < 11:
            print(f"   ⚠️ Home team starting with only {len(home_players)} players")
        if len(away_players) < 11:
            print(f"   ⚠️ Away team starting with only {len(away_players)} players")

    # 4️⃣ Stadium pitch quality
    stadium_result = await db.execute(select(Stadium).where(Stadium.club_id == home_club.id))
    stadium = stadium_result.scalar_one_or_none()
    pitch_quality = stadium.pitch_quality if stadium else 50

    # =========================================
    # 🕐 NEW: Minute-based event simulation with immediate send-offs
    # =========================================
    if TEST_MODE:
        print(f"\n🏁 Starting async match simulation: {home_club.name} vs {away_club.name}")
        print(f"   Initial squad sizes: Home={len(home_players)}, Away={len(away_players)}")

    match_events = await simulate_minute_based_events_async(home_players, away_players)
    
    home_goals = match_events["home_goals"]
    away_goals = match_events["away_goals"]
    bookings_payload = match_events["bookings_with_minutes"]
    send_offs = match_events["send_offs"]
    
    if TEST_MODE:
        print(f"   Final score: {home_goals}-{away_goals}")
        print(f"   Total bookings: {len(bookings_payload)}")
        print(f"   Players sent off: {len(send_offs)}")

    # 5️⃣ Update fixture with results
    fixture.home_goals = home_goals
    fixture.away_goals = away_goals
    fixture.is_played = True
    fixture.match_time = datetime.utcnow()

    # =========================================
    # 🟥 NEW: Create suspensions AFTER match ends
    # =========================================
    newly_suspended_players = set()
    
    # Process send-offs and create suspensions
    for send_off in send_offs:
        player_id = send_off["player_id"]
        reason = send_off["reason"]
        
        if reason == "second_yellow":
            suspension_length = TWO_YELLOWS_SUSPENSION
            await create_or_update_suspension(db, player_id, suspension_length, "two_yellows")
            
            newly_suspended_players.add(player_id)
            if TEST_MODE:
                print(f"   📋 Created {suspension_length}-match suspension for player {player_id} (two yellows)")
                
        elif reason == "direct_red":
            suspension_length = random.randint(RED_SUSPENSION_MIN, RED_SUSPENSION_MAX)
            await create_or_update_suspension(db, player_id, suspension_length, "red_card")
            newly_suspended_players.add(player_id)
            if TEST_MODE:
                print(f"   📋 Created {suspension_length}-match suspension for player {player_id} (red card)")

    # =========================================
    # 📉 Decrement existing suspensions (but skip this match's new ones)
    # =========================================
    if TEST_MODE and newly_suspended_players:
        print(f"   🔄 Decrementing existing suspensions (skipping {len(newly_suspended_players)} new ones)")
    
    await decrement_suspensions_after_match(db, fixture.home_club_id, fixture.away_club_id)

    # 6️⃣ Injury & Reinjury Risk Logic (only for players who weren't sent off)
    injuries = []
    base_risk = 0.05  # Baseline injury risk (5%)
    all_players = list(home_players) + list(away_players)
    active_at_end = set(match_events["final_active_players"]["home"] + match_events["final_active_players"]["away"])

    for player in all_players:
        # Skip injury calculation for players who were sent off
        if player.id not in active_at_end:
            if TEST_MODE:
                print(f"   🚫 Skipping injury risk for sent-off player: {player.first_name} {player.last_name}")
            continue

        # Placeholder fatigue and injury proneness (future systems will enhance this)
        energy = 100  
        injury_proneness = 1.0  

        # Check for existing rehab injury
        rehab_injury = await db.execute(
            select(Injury).where(Injury.player_id == player.id, Injury.days_remaining > 0)
        )
        rehab_injury = rehab_injury.scalar_one_or_none()

        # Calculate risk
        risk = calculate_injury_risk(base_risk, pitch_quality, energy, injury_proneness)

        if rehab_injury and rehab_injury.days_remaining <= rehab_injury.rehab_start:
            risk *= REINJURY_MULTIPLIER  # ✅ Config-driven multiplier
            if TEST_MODE:
                print(f"   - Applied Reinjury Multiplier: x{REINJURY_MULTIPLIER}")

        if TEST_MODE:
            print(f"[DEBUG] Injury Check: {player.first_name} {player.last_name}")
            print(f"   - Base Risk: {base_risk*100:.2f}%")
            print(f"   - Pitch Quality: {pitch_quality}")
            print(f"   - Energy: {energy}")
            print(f"   - Rehab Phase: {'Yes' if rehab_injury else 'No'}")
            print(f"   - Final Risk: {risk*100:.2f}%")

        # Roll for injury
        if random.random() < risk:
            new_injury_data = generate_injury()
            tz = timezone(timedelta(hours=2))

            # If reinjury during rehab: overwrite injury details
            if rehab_injury:
                rehab_injury.name = new_injury_data["name"]
                rehab_injury.type = new_injury_data["type"]
                rehab_injury.severity = new_injury_data["severity"]
                rehab_injury.start_date = datetime.now(tz)
                rehab_injury.days_total = new_injury_data["days_total"]
                rehab_injury.rehab_start = new_injury_data["rehab_start"]
                rehab_injury.rehab_xp_multiplier = new_injury_data["rehab_xp_multiplier"]
                rehab_injury.fit_for_matches = False
                rehab_injury.days_remaining = new_injury_data["days_total"]
                if TEST_MODE:
                    print(f"   🔁 Reinjury Event: {player.first_name} {player.last_name} aggravated an existing injury during the match!")
            else:
                # Fresh injury assignment
                new_injury = Injury(
                    player_id=player.id,
                    name=new_injury_data["name"],
                    type=new_injury_data["type"],
                    severity=new_injury_data["severity"],
                    start_date=datetime.now(tz),
                    days_total=new_injury_data["days_total"],
                    rehab_start=new_injury_data["rehab_start"],
                    rehab_xp_multiplier=new_injury_data["rehab_xp_multiplier"],
                    fit_for_matches=new_injury_data["fit_for_matches"],
                    days_remaining=new_injury_data["days_total"]
                )
                db.add(new_injury)

            # Log injury for summary
            club_result = await db.execute(select(Club).where(Club.id == player.club_id))
            player_club = club_result.scalar_one()

            print(
                f"[{datetime.now(tz)}] 🩺 Injury Logged: "
                f"{player.first_name} {player.last_name} "
                f"({player_club.name}) suffered '{new_injury_data['name']}' "
                f"({new_injury_data['severity']}, {new_injury_data['days_total']} days)"
            )

            injuries.append({
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                "reinjury": bool(rehab_injury),  # ✅ True if aggravated an existing rehab injury
                **new_injury_data
            })

    # Final commit of all changes
    await db.commit()
    await db.refresh(fixture)
    
    if TEST_MODE:
        total_injuries = len(injuries)
        reinjury_count = sum(1 for inj in injuries if inj["reinjury"])
        print(f"\n📊 Async Match Summary:")
        print(f"   Score: {home_goals}-{away_goals}")
        print(f"   Injuries: {total_injuries} total ({total_injuries - reinjury_count} new, {reinjury_count} reinjuries)")
        print(f"   Send-offs: {len(send_offs)}")
        print(f"   New suspensions: {len(newly_suspended_players)}")
        print(f"   Fixture ID: {fixture.id}")
        print("🏁 Async match simulation complete!\n")

    return {
        "fixture_id": fixture.id,
        "home_club_id": fixture.home_club_id,
        "away_club_id": fixture.away_club_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "played_at": fixture.match_time,
        "injuries": injuries,
        "bookings": bookings_payload,
        "send_offs": send_offs,
        
        # NEW: Formation information with squad details
        "formations": {
            "home": {
                "formation_name": home_squad_info["formation_info"]["formation_name"],
                "has_formation": home_squad_info["formation_info"]["has_formation"],
                "starting_players": len(home_players),  # ✅ Shows actual count (7-11)
                "match_squad_size": home_squad_info["match_squad_size"],
                "assigned_count": home_squad_info["formation_info"]["assigned_count"],
                "auto_filled": home_squad_info["formation_info"]["auto_filled"]
            },
            "away": {
                "formation_name": away_squad_info["formation_info"]["formation_name"],
                "has_formation": away_squad_info["formation_info"]["has_formation"],
                "starting_players": len(away_players),  # ✅ Shows actual count (7-11)
                "match_squad_size": away_squad_info["match_squad_size"],
                "assigned_count": away_squad_info["formation_info"]["assigned_count"],
                "auto_filled": away_squad_info["formation_info"]["auto_filled"]
            }
        }
    }


# =========================================
# 🕐 NEW: Async minute-based event simulation
# =========================================
async def simulate_minute_based_events_async(home_players, away_players) -> dict:
    """
    Simulates minute-by-minute events with proper 7-player rule enforcement.
    """
    from typing import Set
    
    # Track which players are still on the pitch (start with all 11 from each team)
    home_active: Set[int] = {p.id for p in home_players}
    away_active: Set[int] = {p.id for p in away_players}
    
    # Track bookings throughout the match
    home_yellows = {}
    away_yellows = {}
    
    # Store events
    bookings_with_minutes = []
    send_offs = []
    
    # Match state
    match_abandoned = False
    abandonment_reason = ""
    abandonment_minute = 90
    
    # Simulate goals
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)
    
    # Simulate events throughout 90 minutes
    for minute in range(1, 91):
        # ✅ ENFORCE 7-PLAYER RULE
        if len(home_active) < 7:
            match_abandoned = True
            abandonment_reason = f"Home team insufficient players (minute {minute})"
            abandonment_minute = minute
            # Away team wins 3-0
            home_goals = 0
            away_goals = 3
            break
        elif len(away_active) < 7:
            match_abandoned = True
            abandonment_reason = f"Away team insufficient players (minute {minute})"
            abandonment_minute = minute
            # Home team wins 3-0
            home_goals = 3
            away_goals = 0
            break
        
        # Random chance of booking each minute (reduced rate for realism)
        if random.random() < 0.01:  # 1% chance per minute (was 2%)
            # Pick a random team that still has players
            teams_available = []
            if home_active:
                teams_available.append("home")
            if away_active:
                teams_available.append("away")
            
            if not teams_available:
                break  # No players left (shouldn't happen due to 7-player check)
            
            team = random.choice(teams_available)
            
            if team == "home" and home_active:
                player_id = random.choice(list(home_active))
                
                if random.random() < 0.15:  # 15% chance of direct red
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "red"
                    })
                    send_offs.append({
                        "player_id": player_id,
                        "minute": minute,
                        "reason": "direct_red"
                    })
                    home_active.discard(player_id)
                    if TEST_MODE:
                        print(f"   🟥 MINUTE {minute}: Player {player_id} (HOME) sent off! Home now has {len(home_active)} players")
                else:  # Yellow card
                    home_yellows[player_id] = home_yellows.get(player_id, 0) + 1
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "yellow"
                    })
                    
                    if home_yellows[player_id] >= 2:  # Second yellow = red
                        bookings_with_minutes.append({
                            "player_id": player_id,
                            "minute": minute,
                            "type": "second_yellow_red"
                        })
                        send_offs.append({
                            "player_id": player_id,
                            "minute": minute,
                            "reason": "second_yellow"
                        })
                        home_active.discard(player_id)
                        if TEST_MODE:
                            print(f"   🟥 MINUTE {minute}: Player {player_id} (HOME) second yellow! Home now has {len(home_active)} players")
            
            elif team == "away" and away_active:
                # Same logic for away team
                player_id = random.choice(list(away_active))
                
                if random.random() < 0.15:  # Direct red
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "red"
                    })
                    send_offs.append({
                        "player_id": player_id,
                        "minute": minute,
                        "reason": "direct_red"
                    })
                    away_active.discard(player_id)
                    if TEST_MODE:
                        print(f"   🟥 MINUTE {minute}: Player {player_id} (AWAY) sent off! Away now has {len(away_active)} players")
                else:  # Yellow card
                    away_yellows[player_id] = away_yellows.get(player_id, 0) + 1
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "yellow"
                    })
                    
                    if away_yellows[player_id] >= 2:  # Second yellow = red
                        bookings_with_minutes.append({
                            "player_id": player_id,
                            "minute": minute,
                            "type": "second_yellow_red"
                        })
                        send_offs.append({
                            "player_id": player_id,
                            "minute": minute,
                            "reason": "second_yellow"
                        })
                        away_active.discard(player_id)
                        if TEST_MODE:
                            print(f"   🟥 MINUTE {minute}: Player {player_id} (AWAY) second yellow! Away now has {len(away_active)} players")
    
    return {
        "home_goals": home_goals,
        "away_goals": away_goals,
        "bookings_with_minutes": bookings_with_minutes,
        "send_offs": send_offs,
        "match_abandoned": match_abandoned,
        "abandonment_reason": abandonment_reason,
        "abandonment_minute": abandonment_minute,
        "final_active_players": {
            "home": list(home_active),
            "away": list(away_active)
        }
    }


# =========================================
# 📉 NEW: Async suspension countdown with smart exclusion
# =========================================
async def decrement_suspensions_after_match_async(db: AsyncSession, home_club_id: int, away_club_id: int, newly_suspended_players: Set[int]) -> None:
    """
    Decrements matches_remaining for all players with active suspensions
    in either the home or away club for the just-played match.
    
    NEW: Skip players who got suspended in THIS match (newly_suspended_players)
    so their suspension countdown doesn't start until the NEXT match.
    """
    # Find all Suspension rows for players in either club with matches_remaining > 0
    stmt = (
        select(Suspension)
        .join(Player, Player.id == Suspension.player_id)
        .where(
            Player.club_id.in_([home_club_id, away_club_id]),
            Suspension.matches_remaining > 0
        )
    )
    result = await db.execute(stmt)
    suspensions = result.scalars().all()

    # Decrement each suspension, but skip players who got suspended this match
    changed = False
    for sus in suspensions:
        # Skip players who got suspended in this same match
        if sus.player_id in newly_suspended_players:
            if TEST_MODE:
                print(f"   ⏭️  Skipping suspension decrement for player {sus.player_id} (suspended this match)")
            continue
            
        sus.matches_remaining = max(0, sus.matches_remaining - 1)
        sus.updated_at = datetime.utcnow()
        db.add(sus)
        changed = True
        
        if TEST_MODE:
            print(f"   ⏬ Player {sus.player_id} suspension decremented to {sus.matches_remaining} matches")

# ---------------------------------------------
# Helper: add/update a suspension for a player
# ---------------------------------------------
async def create_or_update_suspension(db: AsyncSession, player_id: int, matches: int, reason: str):
    """
    Creates a new Suspension or adds matches onto an existing one.
    - If there's any existing Suspension row for this player, we ADD to matches_remaining.
    - Otherwise, we create a fresh suspension.
    """
    # Find any suspension rows for this player
    result = await db.execute(
        select(Suspension).where(Suspension.player_id == player_id)
    )
    existing = result.scalars().first()

    if existing:
        existing.matches_remaining = max(0, existing.matches_remaining) + max(0, matches)
        existing.total_matches_suspended += max(0, matches)  # NEW: Track total
        existing.reason = reason
        existing.updated_at = datetime.utcnow()
        db.add(existing)
    else:
        sus = Suspension(
            player_id=player_id,
            reason=reason,
            matches_remaining=max(0, matches),
            total_matches_suspended=max(0, matches)  # NEW: Track total
        )
        db.add(sus)

    await db.commit()

# ------------------------------------------------------------
# Suspension countdown per match
# ------------------------------------------------------------
async def decrement_suspensions_after_match(db: AsyncSession, home_club_id: int, away_club_id: int) -> None:
    """
    Decrements matches_remaining for all players with active suspensions
    in either the home or away club for the just-played match.
    """
    # Find all Suspension rows for players in either club with matches_remaining > 0
    stmt = (
        select(Suspension)
        .join(Player, Player.id == Suspension.player_id)
        .where(
            Player.club_id.in_([home_club_id, away_club_id]),
            Suspension.matches_remaining > 0
        )
    )
    result = await db.execute(stmt)
    suspensions = result.scalars().all()

    # Decrement each and stage for commit
    changed = False  # ✅ ADD THIS LINE
    for sus in suspensions:
        sus.matches_remaining = max(0, sus.matches_remaining - 1)
        sus.updated_at = datetime.utcnow()
        db.add(sus)
        changed = True  # ✅ ADD THIS LINE

    # Commit changes if any
    if changed:
        await db.commit()