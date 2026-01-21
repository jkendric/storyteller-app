from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

from app.config import get_settings

settings = get_settings()

# Ensure data directory exists
db_path = settings.database_url.replace("sqlite:///", "")
Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations():
    """Run database migrations for schema changes."""
    with engine.connect() as conn:
        # Check if stories table exists
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stories'"
        ))
        if not result.fetchone():
            return  # Table doesn't exist yet, will be created by create_all

        # Check existing columns in stories table
        result = conn.execute(text("PRAGMA table_info(stories)"))
        existing_columns = {row[1] for row in result.fetchall()}

        # Add story generation settings columns if they don't exist
        migrations = [
            ("target_word_preset", "VARCHAR(20) DEFAULT 'medium'"),
            ("temperature", "FLOAT DEFAULT 0.7"),
            ("writing_style", "VARCHAR(20) DEFAULT 'balanced'"),
            ("mood", "VARCHAR(20) DEFAULT 'moderate'"),
            ("pacing", "VARCHAR(20) DEFAULT 'moderate'"),
        ]

        for column_name, column_def in migrations:
            if column_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE stories ADD COLUMN {column_name} {column_def}"))
                conn.commit()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    # Run migrations for existing tables
    _run_migrations()
