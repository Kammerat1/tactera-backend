import openpyxl
from sqlmodel import Session
from database import engine
from models import StatLevelRequirement
from sqlalchemy import text

# Path to your latest Excel file (update if it's named differently)
EXCEL_FILE_PATH = "Training_xp_levels_uploaded.xlsx"

def seed_statlevel_table_from_excel():
    # Load the Excel workbook
    workbook = openpyxl.load_workbook(EXCEL_FILE_PATH)
    sheet = workbook.active

    # Start a session to write to the database
    with Session(engine) as session:
        # Optional: Clear existing data first
        session.exec(text("DELETE FROM statlevelrequirement"))
        session.commit()

        # Loop through rows starting from the second row (skip header)
        for row in sheet.iter_rows(min_row=2, max_col=2, values_only=True):
            level, xp_required = row

            # Skip rows that are missing either value
            if level is None or xp_required is None:
                continue

            # Insert new StatLevelRequirement row
            session.add(StatLevelRequirement(level=int(level), xp_required=int(xp_required)))

        session.commit()
        print("✅ XP levels seeded from Excel.")

if __name__ == "__main__":
    seed_statlevel_table_from_excel()
