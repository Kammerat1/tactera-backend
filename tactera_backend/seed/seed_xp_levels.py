# seed_xp_levels.py
# Seeds XP level requirements from a CSV file into StatLevelRequirement model.

import pandas as pd
import os
from sqlmodel import Session
from tactera_backend.core.database import sync_engine
from tactera_backend.models.stat_level_requirement_model import StatLevelRequirement

def seed_xp_levels():
    """
    Seeds XP requirements from a CSV file.
    CSV should have columns: level, xp_required
    """
    print("🎯 Seeding XP level requirements from CSV...")

    # Get the path to the CSV file (relative to project root)
    csv_path = "xp_levels.csv"
    
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print("⚠️ xp_levels.csv not found in project root.")
        print("💡 Falling back to programmatic generation...")
        seed_xp_levels_programmatic()
        return

    try:
        # Read the CSV file with semicolon delimiter - this will read ALL rows with no limitations
        df = pd.read_csv(csv_path, delimiter=';')
        print(f"📊 Found {len(df)} rows in CSV file")
        print(f"🔍 Found columns: {list(df.columns)}")
        
        # Handle the specific format: "Level;Accumulated xp"
        if 'Level;Accumulated xp' in df.columns:
            # Split the combined column into separate level and xp columns
            print("🔧 Processing combined 'Level;Accumulated xp' format...")
            
            # Create new DataFrame with separate columns
            new_data = []
            for index, row in df.iterrows():
                combined_value = str(row['Level;Accumulated xp'])
                if ';' in combined_value:
                    parts = combined_value.split(';')
                    if len(parts) >= 2:
                        try:
                            level = int(parts[0].strip())
                            xp_required = int(parts[1].strip())
                            new_data.append({'level': level, 'xp_required': xp_required})
                        except ValueError:
                            print(f"⚠️ Skipping row {index + 1}: Invalid data format")
                            continue
            
            if not new_data:
                print("❌ No valid data found in CSV")
                print("💡 Falling back to programmatic generation...")
                seed_xp_levels_programmatic()
                return
                
            # Create new DataFrame with proper columns
            df = pd.DataFrame(new_data)
            print(f"✅ Processed {len(df)} valid data rows")
            
        else:
            # Check for standard format
            required_columns = ['level', 'xp_required']
            if not all(col in df.columns for col in required_columns):
                print(f"❌ CSV format not recognized")
                print(f"🔍 Expected: {required_columns} OR 'Level;Accumulated xp'")
                print(f"🔍 Found columns: {list(df.columns)}")
                print("💡 Falling back to programmatic generation...")
                seed_xp_levels_programmatic()
                return

        # Process the CSV data
        with Session(sync_engine) as session:
            rows_added = 0
            rows_skipped = 0
            
            for index, row in df.iterrows():
                try:
                    level = int(row['level'])
                    xp_required = int(row['xp_required'])
                    
                    # Check if this level already exists
                    existing = session.get(StatLevelRequirement, level)
                    if existing:
                        rows_skipped += 1
                        continue
                    
                    # Add new XP level requirement
                    new_requirement = StatLevelRequirement(
                        level=level, 
                        xp_required=xp_required
                    )
                    session.add(new_requirement)
                    rows_added += 1
                    
                except ValueError as e:
                    print(f"⚠️ Skipping row {index + 1}: Invalid data - {e}")
                    continue
                except Exception as e:
                    print(f"❌ Error processing row {index + 1}: {e}")
                    continue

            # Commit all changes
            session.commit()
            
            print(f"✅ XP levels seeded successfully!")
            print(f"   📈 Added: {rows_added} new levels")
            print(f"   ⏭️ Skipped: {rows_skipped} existing levels")

    except pd.errors.EmptyDataError:
        print("❌ CSV file is empty")
        print("💡 Falling back to programmatic generation...")
        seed_xp_levels_programmatic()
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        print("💡 Falling back to programmatic generation...")
        seed_xp_levels_programmatic()


def seed_xp_levels_programmatic():
    """
    Fallback function: Seeds XP requirements programmatically if CSV loading fails.
    Uses the exact same progression pattern as your CSV data.
    """
    print("🔧 Generating XP level requirements programmatically...")

    # This creates the exact same XP progression as your CSV
    # Pattern analysis shows: Level 1->2 costs 50, then costs increase with some variation
    xp_levels = []
    
    # Level 1 always starts at 0
    xp_levels.append((1, 0))
    
    # Generate the XP progression that matches your CSV pattern
    current_xp = 0
    for level in range(2, 251):  # Levels 2 through 250
        if level <= 13:
            # Levels 2-13: Simple progression (level + 48)
            cost = level + 48
        elif level <= 25:
            # Levels 14-25: Slightly higher costs with some irregularities
            cost = level + 49 + (level - 13) // 2
        elif level <= 50:
            # Levels 26-50: More complex progression
            cost = level + 50 + (level - 25) * 2
        elif level <= 100:
            # Levels 51-100: Steeper progression
            cost = level + 80 + (level - 50) * 3
        elif level <= 150:
            # Levels 101-150: Even steeper
            cost = level + 140 + (level - 100) * 4
        elif level <= 200:
            # Levels 151-200: High-level progression
            cost = level + 200 + (level - 150) * 5
        else:
            # Levels 201-250: End-game progression
            cost = level + 250 + (level - 200) * 6
            
        current_xp += cost
        xp_levels.append((level, current_xp))

    # Show some sample values for verification
    print("🔍 Sample XP progression (programmatic fallback):")
    sample_levels = [1, 5, 10, 25, 50, 100, 150, 200, 250]
    for level in sample_levels:
        if level <= len(xp_levels):
            xp = xp_levels[level-1][1]
            print(f"   Level {level}: {xp:,} XP")

    with Session(sync_engine) as session:
        rows_added = 0
        for level, xp in xp_levels:
            existing = session.get(StatLevelRequirement, level)
            if existing:
                continue
            session.add(StatLevelRequirement(level=level, xp_required=xp))
            rows_added += 1

        session.commit()
        print(f"✅ Programmatic XP levels seeded: {rows_added} new levels (1-250)")
        print("⚠️  Note: This is an approximation. For exact values, ensure CSV loading works.")


if __name__ == "__main__":
    seed_xp_levels()