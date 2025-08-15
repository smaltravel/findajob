from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.loader import settings
from app.models import Base

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


create_tables()
