# app/middleware/request_id.py
import logging
import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

# Контекстная переменная для хранения request_id в рамках одного запроса
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Добавляет/пробрасывает X-Request-ID и внедряет его в логи."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("psychology-api.middleware")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        # Сохраняем в контекст для доступа из любого места
        token = request_id_var.set(request_id)

        # Логируем начало запроса
        self.logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        # Функция-обёртка для перехвата ответа и логирования статуса
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                level = logging.ERROR if status_code >= 500 else logging.INFO
                self.logger.log(
                    level,
                    "Request completed",
                    extra={
                        "request_id": request_id,
                        "status_code": status_code,
                        "method": request.method,
                        "path": request.url.path,
                    },
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)


def get_request_id() -> str:
    """Возвращает текущий request_id из контекста."""
    return request_id_var.get()


class RequestIDFilter(logging.Filter):
    """Фильтр для автоматического добавления request_id в каждую запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True