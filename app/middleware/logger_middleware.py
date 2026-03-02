import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger
from app.core.log_context import request_id_var, current_user_id_var

class RequestLoggingMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    # Встановлюємо контекстні змінні для request_id та user_id
    token_request = request_id_var.set(str(uuid.uuid4()))
    token_user = current_user_id_var.set(None)

    try:
      start = time.time()
      response = await call_next(request)
      duration = time.time() - start

      logger.info(
        f"{request.method} {request.url.path} completed in {duration:.3f}s "
        f"status_code={response.status_code}"
      )

      return response

    finally:
      # очищаємо контекст після запиту
      request_id_var.reset(token_request)
      current_user_id_var.reset(token_user)
