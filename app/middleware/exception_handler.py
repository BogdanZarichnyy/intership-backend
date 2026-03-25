from typing import Callable, Awaitable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler
from app.core.logger import logger
from app.core.exceptions_base import APIException

# Загальний тип для асинхронних обробників
ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

# =======================
# HTTPException
# =======================
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
  logger.error(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
  return JSONResponse(
    status_code=exc.status_code,
    content={"detail": exc.detail}
  )

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
