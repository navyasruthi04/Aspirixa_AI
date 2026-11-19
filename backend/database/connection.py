from pathlib import Path  #imports Python's path-handling tool.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# Find the main Aspirixa_AI project folder
BASE_DIR = Path(__file__).resolve().parents[2]  #finds our main project folder:

# Location of our SQLite database
DATABASE_PATH = BASE_DIR / "database" / "aspirixa.db" #Aspirixa_AI/database/aspirixa.db

# SQLite database URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}" #This tells SQLAlchemy: We are using SQLite and this is where the database file is located.


# Create SQLAlchemy engine
engine = create_engine(           #engine? Think of it as the main connection mechanism between our application and SQLite
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# Create database sessions
SessionLocal = sessionmaker(    #A session is used when our application needs to interact with the database.
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for our database models
class Base(DeclarativeBase):  
    pass


# Database dependency for FastAPI
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()