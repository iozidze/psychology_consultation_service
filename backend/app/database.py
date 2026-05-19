# app/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import settings

# 🔧 Оптимизация пула соединений для контейнеров
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=5,         # Ограничиваем пул для контейнера
    max_overflow=10,
    pool_recycle=3600,   # Переподключение каждые 1 час
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Гарантированное закрытие сессии


def close_all_connections():
    """Закрытие всех соединений пула."""
    SessionLocal.close_all()
    engine.dispose()