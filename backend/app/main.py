# app/main.py
import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.routes import auth, users, slots, notes
from app.seed import seed_database
from app.logging_config import setup_logging, get_logger
from app.middleware.request_id import RequestIDMiddleware, RequestIDFilter

# Настройка логирования
setup_logging(log_level=settings.log_level)
logger = get_logger("psychology-api.main")
logging.getLogger().addFilter(RequestIDFilter())

# 🔄 Флаг для остановки приёма новых запросов
_is_shutting_down = False


def set_shutting_down(flag: bool):
    global _is_shutting_down
    _is_shutting_down = flag


def is_shutting_down() -> bool:
    return _is_shutting_down


# 🚫 Middleware для отказа в новых запросах при shutdown
class ShutdownMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and is_shutting_down():
            response = JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Service is shutting down"}
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


def initialize_database() -> None:
    last_error = None
    for attempt in range(settings.db_connect_retries):
        try:
            logger.info("Attempting database connection", extra={"attempt": attempt + 1})
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                seed_database(db)
                logger.info("Database seeded successfully")
            finally:
                db.close()
            logger.info("Database initialized")
            return
        except OperationalError as exc:
            logger.error("Database connection failed", extra={"error": str(exc), "attempt": attempt + 1})
            last_error = exc
            asyncio.sleep(settings.db_connect_retry_delay)
    logger.critical("Failed to connect to database after all retries")
    raise last_error


async def cleanup_resources():
    """Очистка ресурсов при завершении работы."""
    logger.info("Starting graceful shutdown cleanup...")
    
    # Закрываем все активные сессии БД
    SessionLocal.close_all()
    
    # Закрываем пул соединений
    if engine:
        engine.dispose()
        logger.info("Database connections closed")
    
    # Здесь можно добавить очистку других ресурсов:
    # - Redis подключения
    # - Фоновые задачи
    # - WebSocket соединения
    
    logger.info("Cleanup completed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan контекст для startup/shutdown логики."""
    # === STARTUP ===
    logger.info("Application starting", extra={"port": settings.port})
    initialize_database()
    
    # Регистрация обработчиков сигналов
    loop = asyncio.get_event_loop()
    
    def handle_shutdown_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        set_shutting_down(True)
        # Uvicorn сам обработает SIGTERM, мы только ставим флаг
    
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    
    yield  # ⏸️ Приложение работает
    
    # === SHUTDOWN ===
    set_shutting_down(True)
    logger.info("Application shutting down, waiting for in-flight requests...")
    
    # Даём время завершиться текущим запросам (настраивается в stop_grace_period)
    await asyncio.sleep(2)
    
    # Очищаем ресурсы
    await cleanup_resources()
    
    logger.info("Application shutdown complete")


app = FastAPI(title="Psychology Consultation Service", lifespan=lifespan)

# ⚠️ ВАЖНО: в FastAPI middleware выполняется в ОБРАТНОМ порядке добавления!
# Последний add_middleware вызывается ПЕРВЫМ.

# 1️⃣ ShutdownMiddleware — добавляем ПЕРВЫМ, выполнится ПОСЛЕДНИМ
app.add_middleware(ShutdownMiddleware)

# 2️⃣ RequestIDMiddleware — добавляем ВТОРЫМ, выполнится ВТОРЫМ
app.add_middleware(RequestIDMiddleware)

# 3️⃣ CORSMiddleware — добавляем ПОСЛЕДНИМ, выполнится ПЕРВЫМ (обрабатывает OPTIONS preflight)
allowed_origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(slots.router)
app.include_router(notes.router)


@app.get("/")
def root():
    if is_shutting_down():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"message": "Service is shutting down"}
        )
    logger.debug("Health check endpoint called")
    return {"message": "API is running"}


@app.get("/health")
def health_check():
    """Эндпоинт для Kubernetes/оркестратора."""
    if is_shutting_down():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "shutting_down"}
        )
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
