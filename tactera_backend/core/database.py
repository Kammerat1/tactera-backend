import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Absolute database path ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DB_PATH = os.path.join(BASE_DIR, "tactera.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"  # Async SQLite URL
from sqlalchemy import create_engine as create_sync_engine  # ADD THIS

# Create a separate sync engine for seeding
sync_engine = create_sync_engine(f"sqlite:///{DB_PATH}", echo=True, future=True)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Create async session maker
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get DB session (for FastAPI routes)
async def get_db():
    async with async_session_maker() as session:
        yield session

# Initialize DB (async safe)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Optional: Sync session (for seed scripts or non-async usage)
from sqlmodel import Session
def get_sync_session():
    return Session(engine.sync_engine)  # Access sync engine from async engine


# Legacy support: get_session (sync) for modules like auth.py
from sqlmodel import Session

def get_session():
    """Legacy sync session dependency for older parts of the code (e.g., auth)."""
    with Session(engine.sync_engine) as session:
        yield session
