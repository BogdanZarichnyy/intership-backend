from typing import Callable, Awaitable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler as default_http_handler
from app.core.logger import logger
from app.core.exceptions import *  # Наші кастомні помилки
from fastapi import status

# Загальний тип для асинхронних обробників
ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

# =======================
# Базовий клас та стандартні HTTP-помилки
# =======================
class APIException(Exception):
  """Базовий клас для всіх кастомних помилок з HTTP статусом"""
  status_code: int = status.HTTP_400_BAD_REQUEST
  detail: str = "An error occurred"

  def __init__(self, detail: str | None = None):
    if detail:
      self.detail = detail
    super().__init__(self.detail)

class BadRequest(APIException):
  status_code = status.HTTP_400_BAD_REQUEST

class Unauthorized(APIException):
  status_code = status.HTTP_401_UNAUTHORIZED

class Forbidden(APIException):
  status_code = status.HTTP_403_FORBIDDEN

class NotFound(APIException):
  status_code = status.HTTP_404_NOT_FOUND

class MethodNotAllowed(APIException):
  status_code = status.HTTP_405_METHOD_NOT_ALLOWED

class Conflict(APIException):
  status_code = status.HTTP_409_CONFLICT

class TooManyRequests(APIException):
  status_code = status.HTTP_429_TOO_MANY_REQUESTS

class InternalServerError(APIException):
  status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

class ServiceUnavailable(APIException):
  status_code = status.HTTP_503_SERVICE_UNAVAILABLE

# =======================
# HTTPException
# =======================
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
  logger.error(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
  return await default_http_handler(request, exc)

# =======================
# RequestValidationError
# =======================
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
  logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
  return JSONResponse(
    status_code=422,
    content=jsonable_encoder({"detail": exc.errors(), "body": exc.body})
  )

# =======================
# APIException
# =======================
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
  logger.error(f"Business error on {request.url.path}: {exc.detail}")
  return JSONResponse(
    status_code=exc.status_code,
    content={"detail": exc.detail}
  )

# =======================
# Функція для підключення всіх глобальних хендлерів
# =======================
def setup_exception_handlers(app: FastAPI) -> None:
  app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
  app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
  app.add_exception_handler(APIException, api_exception_handler)  # type: ignore[arg-type]
