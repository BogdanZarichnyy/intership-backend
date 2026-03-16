from app.middleware.exception_handler import (
  APIException,
  BadRequest,
  Unauthorized,
  Forbidden,
  NotFound,
  MethodNotAllowed,
  Conflict,
  TooManyRequests,
  InternalServerError,
  ServiceUnavailable,
)

# =======================
# Users
# =======================
class UserNotFound(NotFound):
  def __init__(self, detail: str = "User not found"):
    super().__init__(detail)

class ForbiddenAction(Forbidden):
  def __init__(self, detail: str = "Not authorized to perform this action"):
    super().__init__(detail)

class ExistsEmail(Conflict):
  def __init__(self, email: str | None = None):
    detail = f"User with email '{email}' already exists" if email else "User with this email already exists"
    super().__init__(detail)

class ExistsUsername(Conflict):
  def __init__(self, username: str):
    super().__init__(f"Username '{username}' already exists.")

class InvalidPassword(BadRequest):
  def __init__(self, detail: str = "Current password is incorrect"):
    super().__init__(detail)

class MissingCurrentPassword(BadRequest):
  def __init__(self, detail: str = "Current password must be provided"):
    super().__init__(detail)

class MissingNewPassword(BadRequest):
  def __init__(self, detail: str = "New password must be provided"):
    super().__init__(detail)

# =======================
# Authorization
# =======================
class InvalidCredentials(Unauthorized):
  def __init__(self, detail: str = "Invalid credentials"):
    super().__init__(detail)

class InvalidToken(Unauthorized):
  def __init__(self, detail: str = "Invalid token"):
    super().__init__(detail)

class InvalidTokenType(Unauthorized):
  def __init__(self, detail: str = "Invalid token type"):
    super().__init__(detail)

class InvalidTokenPayload(Unauthorized):
  def __init__(self, detail: str = "Invalid token payload"):
    super().__init__(detail)

class UserDisabled(Forbidden):
  def __init__(self, detail: str = "User account is disabled"):
    super().__init__(detail)

class AuthProviderUnknown(Conflict):
  def __init__(self, detail: str = "Unknown provider"):
    super().__init__(detail)

class MissingIdToken(Unauthorized):
  def __init__(self, detail: str = "Missing id_token"):
    super().__init__(detail)

class InvalidAuth0Token(Unauthorized):
  def __init__(self, detail: str = "Invalid Auth0 token"):
    super().__init__(detail)

class EmailNotVerified(Forbidden):
  def __init__(self, detail: str = "Email not verified"):
    super().__init__(detail)

class EmailNotFoundInToken(Unauthorized):
  def __init__(self, detail: str = "Email not found in token"):
    super().__init__(detail)

# =======================
# Company
# =======================
class CompanyNotFound(NotFound):
  def __init__(self, detail: str = "Company not found"):
    super().__init__(detail)

class CompanyForbidden(Forbidden):
  def __init__(self, detail: str = "Not enough permissions to access this company"):
    super().__init__(detail)

class CompanyUpdateForbidden(Forbidden):
  def __init__(self, detail: str = "Only owner can update company"):
    super().__init__(detail)

class CompanyDeleteForbidden(Forbidden):
  def __init__(self, detail: str = "Only owner can delete company"):
    super().__init__(detail)

# =======================
# Company members
# =======================
class CompanyOwnerOnly(Forbidden):
  def __init__(self, detail: str = "Only owners can perform this action"):
    super().__init__(detail)

class CompanyMembershipForbidden(Forbidden):
  def __init__(self, detail: str = "You are not allowed to perform this membership action"):
    super().__init__(detail)

# =======================
# Company invitation
# =======================
class InvitationNotFound(NotFound):
  def __init__(self, detail: str = "Invitation not found"):
    super().__init__(detail)

class InvitationAlreadyProcessed(Forbidden):
  def __init__(self, detail: str = "Invitation already processed"):
    super().__init__(detail)

class InvitationForbidden(Forbidden):
  def __init__(self, detail: str = "Action not allowed for this invitation"):
    super().__init__(detail)

# =======================
# Quizzes
# =======================
class QuizNotFound(NotFound):
  def __init__(self, detail: str = "Quiz not found"):
    super().__init__(detail)

class QuizForbidden(Forbidden):
  def __init__(self, detail: str):
    super().__init__(detail)
