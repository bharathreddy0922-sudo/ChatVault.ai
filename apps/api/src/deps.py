from sqlmodel import Session, create_engine, SQLModel
from .config import settings
import os

# Create upload directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)

# Database engine
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
