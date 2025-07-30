from sqlmodel import SQLModel, create_engine, Session
import os
# Delay import to avoid circular import
def import_stat_model():
    from tactera_backend.models.stat_level_requirement import StatLevelRequirement
    return StatLevelRequirement





# --- Absolute database path ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DB_PATH = os.path.join(BASE_DIR, "tactera.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create DB session
def get_session():
    with Session(engine) as session:
        yield session

# Create tables
def init_db():
    StatLevelRequirement = import_stat_model()
    SQLModel.metadata.create_all(engine)
    print("\n=== DEBUG: Using Database File ===")
    print(engine.url)


def get_sync_session():
    """Used outside of FastAPI routes, like in seed scripts."""
    return Session(engine)