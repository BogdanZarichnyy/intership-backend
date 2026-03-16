import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger
from app.core.log_context import request_id_var, current_user_id_var

class RequestLoggingMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    request_token = request_id_var.set(str(uuid.uuid4()))
    user_token = current_user_id_var.set(None)

    try:
      start_time = time.time()
      response = await call_next(request)
      process_time = time.time() - start_time

      logger.info(
        f"{request.method} {request.url.path} completed in "
        f"{process_time:.3f}s status_code={response.status_code}"
      )

      return response

    finally:
      # ВАЖЛИВО: очищаємо контекст
      request_id_var.reset(request_token)
      current_user_id_var.reset(user_token)
