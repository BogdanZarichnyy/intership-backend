from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger
from app.core.exceptions import BusinessError, UserNotFound, ForbiddenAction

# Обробка HTTPException
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
  logger.error(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
  return JSONResponse(
    status_code=exc.status_code,
    content={"detail": exc.detail}
  )

# Обробка помилок валідації
async def validation_exception_handler(request: Request, exc: RequestValidationError):
  logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
  return JSONResponse(
    status_code=422,
    content={"detail": exc.errors()}
  )

# Обробка бізнес-помилок
async def business_error_handler(request: Request, exc: BusinessError):
  logger.error(f"Business error on {request.url.path}: {exc.detail}")

  # мапінг доменних помилок у HTTP-статуси
  if isinstance(exc, UserNotFound):
    status_code = 404
  elif isinstance(exc, ForbiddenAction):
    status_code = 403
  else:
    status_code = 400

  return JSONResponse(
    status_code=status_code,
    content={"detail": exc.detail}
  )
