from contextvars import ContextVar
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger
import time

request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")
current_user_id_var: ContextVar[str | None] = ContextVar("current_user_id", default=None)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    # тут можна отримати user_id якщо є токен авторизації
    user = getattr(request.state, "user", None)
    current_user_id_var.set(getattr(user, "id", None))
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
      f"{request.method} {request.url.path} completed in {process_time:.3f}s "
      f"status_code={response.status_code}"
    )
    return response
