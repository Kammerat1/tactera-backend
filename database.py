from sqlmodel import SQLModel, create_engine, Session

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
    SQLModel.metadata.create_all(engine)
