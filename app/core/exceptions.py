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

class ExistsUsername(HTTPException):
  def __init__(self, username: str):
    super().__init__(
      status_code=409,
      detail=f"Username '{username}' already exists."
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

# Authorization
class InvalidCredentials(HTTPException):
  def __init__(self, detail: str = "Invalid credentials"):
    super().__init__(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=detail
    )

class InvalidToken(HTTPException):
  def __init__(self, detail: str = "Invalid token"):
    super().__init__(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=detail
    )

class InvalidTokenType(HTTPException):
  def __init__(self, detail: str = "Invalid token type"):
    super().__init__(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=detail
    )

class InvalidTokenPayload(HTTPException):
  def __init__(self, detail: str = "Invalid token payload"):
    super().__init__(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=detail
    )

class UserDisabled(HTTPException):
  def __init__(self, detail: str = "User account is disabled"):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=detail
    )

class AuthProviderUnknown(HTTPException):
  def __init__(self, detail: str = "Unknown provider"):
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=detail
    )

class MissingIdToken(HTTPException):
  def __init__(self, detail: str = "Missing id_token"):
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=detail
    )

class InvalidAuth0Token(HTTPException):
  def __init__(self, detail: str = "Invalid Auth0 token"):
    super().__init__(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=detail
    )

class EmailNotVerified(HTTPException):
  def __init__(self, detail: str = "Email not verified"):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=detail
    )

class EmailNotFoundInToken(HTTPException):
  def __init__(self, detail: str = "Email not found in token"):
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=detail
    )

# Company
class CompanyNotFound(HTTPException):
  def __init__(self):
    super().__init__(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Company not found"
    )

class CompanyForbidden(HTTPException):
  def __init__(
    self,
    detail: str = "Not enough permissions to access this company"
  ):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=detail
    )

class CompanyUpdateForbidden(HTTPException):
  def __init__(self):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Only owner can update company"
    )

class CompanyDeleteForbidden(HTTPException):
  def __init__(self):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Only owner can delete company"
    )

# Company members
class CompanyOwnerOnly(HTTPException):
  def __init__(self, detail: str = "Only owners can perform this action"):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=detail
    )


class CompanyMembershipForbidden(HTTPException):
  def __init__(self, detail: str = "You are not allowed to perform this membership action"):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=detail
    )

# Company invitation
class InvitationNotFound(HTTPException):
  def __init__(
    self, 
    detail="Invitation not found"
  ):
    super().__init__(
      status_code=status.HTTP_404_NOT_FOUND, 
      detail=detail
    )

class InvitationAlreadyProcessed(HTTPException):
  def __init__(
      self, 
      detail="Invitation already processed"
    ):
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST, 
      detail=detail
    )

class InvitationForbidden(HTTPException):
  def __init__(
      self, 
      detail="Action not allowed for this invitation"
    ):
    super().__init__(
      status_code=status.HTTP_403_FORBIDDEN, 
      detail=detail
    )
