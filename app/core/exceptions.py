# Base domain exception
class BusinessError(Exception):
  """Base class for domain/business errors"""
  pass

# Users
class ExistsEmail(BusinessError):
  def __init__(self, email: str | None = None):
    self.email = email
    self.detail = (
      f"User with email '{email}' already exists"
      if email else
      "User with this email already exists"
    )
    super().__init__(self.detail)


class ExistsUsername(BusinessError):
  def __init__(self, username: str):
    self.username = username
    self.detail = f"Username '{username}' already exists."
    super().__init__(self.detail)


class InvalidPassword(BusinessError):
  def __init__(self, detail: str = "Current password is incorrect"):
    self.detail = detail
    super().__init__(self.detail)


class MissingCurrentPassword(BusinessError):
  def __init__(self, detail: str = "Current password must be provided"):
    self.detail = detail
    super().__init__(self.detail)


class MissingNewPassword(BusinessError):
  def __init__(self, detail: str = "New password must be provided"):
    self.detail = detail
    super().__init__(self.detail)


class UserNotFound(BusinessError):
  def __init__(self, detail: str = "User not found"):
    self.detail = detail
    super().__init__(self.detail)


class ForbiddenAction(BusinessError):
  def __init__(self, detail: str = "Not authorized to perform this action"):
    self.detail = detail
    super().__init__(self.detail)
