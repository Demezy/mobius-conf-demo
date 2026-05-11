from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# sqlite next to server/
DB_URL = "sqlite:///./mobius.db"

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # local import to keep db.py small
    from models import Event, SessionSummary  # noqa: F401
    Base.metadata.create_all(bind=engine)
