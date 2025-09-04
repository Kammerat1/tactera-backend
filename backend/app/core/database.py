import os
from sqlmodel import SQLModel, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine as create_sync_engine

# --- Absolute database path ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "tactera.db")

# Ensure DB file exists (prevents async context errors)
if not os.path.exists(DB_PATH):
    print("📂 Database file not found. Creating a new one...")
    open(DB_PATH, 'a').close()

# --- Database URLs ---
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"    # Async engine (routes)
SYNC_DATABASE_URL = f"sqlite:///{DB_PATH}"         # Sync engine (seeding/scripts)

# --- Engines ---
engine = create_async_engine(DATABASE_URL, echo=True, future=True)        # Async
sync_engine = create_sync_engine(SYNC_DATABASE_URL, echo=True, future=True)  # Sync

# --- Async session maker ---
async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# --- Async DB session (used in routes) ---
async def get_db():
    async with async_session_maker() as session:
        yield session

# --- Initialize DB tables ---
async def init_db():
    """Create tables asynchronously if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# --- Sync session for seeding/scripts ---
def get_sync_session():
    return Session(sync_engine)

# --- Legacy sync session (for old routes) ---
def get_session():
    with Session(sync_engine) as session:
        yield session
