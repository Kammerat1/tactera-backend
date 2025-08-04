@router.post("/simulate")
def simulate_match(home_email: str, away_email: str, session: Session = Depends(get_session)):
    """
    Simulates a match between two clubs and now includes injury generation.
    - Loads both clubs and players.
    - Calculates match result (shots, goals, possession, etc.).
    - Rolls for injuries based on pitch quality and risk formula.
    """

    # --- Fetch both clubs by manager email ---
    home_club = session.exec(select(Club).where(Club.manager_email == home_email)).first()
    away_club = session.exec(select(Club).where(Club.manager_email == away_email)).first()

    if not home_club or not away_club:
        raise HTTPException(status_code=404, detail="One or both clubs not found.")

    # --- Fetch home club's stadium for pitch quality ---
    stadium = session.exec(select(Stadium).where(Stadium.id == home_club.stadium_id)).first()
    if not stadium:
        raise HTTPException(status_code=404, detail="Stadium for home club not found.")
    pitch_quality = stadium.pitch_quality

    # --- Load players for each club ---
    home_players = session.exec(select(Player).where(Player.club_id == home_club.id)).all()
    away_players = session.exec(select(Player).where(Player.club_id == away_club.id)).all()

    if not home_players or not away_players:
        raise HTTPException(status_code=400, detail="One or both clubs have no players.")

    # --- Calculate average stats for each team ---
    def average(players, stat):
        return sum(getattr(p, stat) for p in players) / len(players)

    home_stats = {
        "pace": average(home_players, "pace"),
        "passing": average(home_players, "passing"),
        "defending": average(home_players, "defending")
    }

    away_stats = {
        "pace": average(away_players, "pace"),
        "passing": average(away_players, "passing"),
        "defending": average(away_players, "defending")
    }

    # --- Match simulation logic (basic goals/shots) ---
    def simulate_team(attack, defense):
        value = (attack + random.uniform(0, 10)) - (defense * 0.5)
        shots = max(1, int(value / 2))
        shots_on_target = max(1, shots - random.randint(0, 3))
        goals = random.randint(0, shots_on_target)
        return shots, shots_on_target, goals

    shots_home, on_target_home, goals_home = simulate_team(
        home_stats["passing"] + home_stats["pace"],
        away_stats["defending"]
    )

    shots_away, on_target_away, goals_away = simulate_team(
        away_stats["passing"] + away_stats["pace"],
        home_stats["defending"]
    )

    # --- Cosmetic stats ---
    possession_home = random.randint(45, 55)
    possession_away = 100 - possession_home
    corners_home = random.randint(2, 7)
    corners_away = random.randint(2, 7)

    # --- Injury logic ---
    injuries = []  # Collect injuries for debugging (later store in DB)
    base_risk = 0.05  # 5% baseline injury chance per player per match
    all_players = home_players + away_players

    for player in all_players:
        energy = 100  # Placeholder (will be dynamic later)
        injury_proneness = 1.0  # Placeholder (hidden stat later)

        # Calculate injury risk using pitch quality
        risk = calculate_injury_risk(base_risk, pitch_quality, energy, injury_proneness)

        # Roll chance: if random < risk, injury happens
        if random.random() < risk:
            injury_data = generate_injury()
            injuries.append({
                "player_id": player.id,
                "player_name": f"{player.first_name} {player.last_name}",
                **injury_data
            })

    # --- Save match result to database ---
    result = MatchResult(
        home_club_id=home_club.id,
        away_club_id=away_club.id,
        home_goals=goals_home,
        away_goals=goals_away,
        possession_home=possession_home,
        possession_away=possession_away,
        corners_home=corners_home,
        corners_away=corners_away,
        shots_home=shots_home,
        shots_away=shots_away,
        shots_on_target_home=on_target_home,
        shots_on_target_away=on_target_away
    )

    session.add(result)
    session.commit()
    session.refresh(result)

    # --- Return match result + injuries (debug for now) ---
    return {
        "match_id": result.id,
        "home_club": home_club.club_name,
        "away_club": away_club.club_name,
        "home_goals": result.home_goals,
        "away_goals": result.away_goals,
        "shots": {"home": result.shots_home, "away": result.shots_away},
        "on_target": {"home": result.shots_on_target_home, "away": result.shots_on_target_away},
        "possession": {"home": result.possession_home, "away": result.possession_away},
        "corners": {"home": result.corners_home, "away": result.corners_away},
        "injuries": injuries  # Debug output for now
    }
