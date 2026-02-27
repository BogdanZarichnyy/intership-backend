from fastapi import HTTPException, status

# Users
class ExistsEmail(HTTPException):
  """Raised when trying to create a user with an existing email"""
  def __init__(
    self,
    email: str | None = None
  ):
    detail = (
      f"User with email '{email}' already exists"
      if email else
      "User with this email already exists"
    )
    super().__init__(
      status_code=status.HTTP_409_CONFLICT,
      detail=detail
    )

class InvalidPassword(HTTPException):
  """Raised when provided password is incorrect"""
  def __init__(
    self,
    detail: str = "Current password is incorrect"
  ):
    super().__init__(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=detail
    )

class MissingCurrentPassword(HTTPException):
  """Raised when current password is required but not provided"""
  def __init__(
    self,
    detail: str = "Current password must be provided"
  ):
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=detail
    )

class MissingNewPassword(HTTPException):
  """Raised when new password is required but not provided"""
  def __init__(
    self,
    detail: str = "New password must be provided"
  ):
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=detail
    )

class UserNotFound(HTTPException):
  """Raised when user does not exist"""
  def __init__(
    self,
    detail: str = "User not found"
  ):
    super().__init__(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=detail
    )

class ForbiddenAction(HTTPException):
  """Raised when user tries to access forbidden resource"""
  def __init__(
    self,
    detail: str = "Not authorized to perform this action"
  ):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=detail
    )
