from fastapi import status

# =======================================
# Базовий клас та стандартні HTTP-помилки
# =======================================
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
