# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal  # 👈 добавьте этот импорт


class Settings(BaseSettings):
    port: int = 8000
    # cors_origins: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,https://psychology-consultation-service.onrender.com,https://psychology-consultation-service-1.onrender.com"

    database_url: str = "postgresql://postgres1:1d7diUVaHy5F5wW2iyrE4tB5DqUp78UH@dpg-d8oroa0k1i2s73ekuidg-a/psychology_qxo6"

    jwt_secret: str = "development-secret-change-me"
    access_token_expire_minutes: int = 1440

    db_connect_retries: int = 30
    db_connect_retry_delay: int = 2
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",          
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # 👈 Важно: позволяет использовать LOG_LEVEL и log_level
    )


settings = Settings()
