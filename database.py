from sqlmodel import SQLModel, create_engine, Session
# Delay import to avoid circular import
def import_stat_model():
    from models import StatLevelRequirement
    return StatLevelRequirement





# SQLite for local dev (use PostgreSQL later)
DATABASE_URL = "sqlite:///./tactera.db"

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

