class BusinessError(Exception):
  """Base class for domain/business errors"""
  pass

# =======================
# Users
# =======================

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

# =======================
# Authorization
# =======================

class InvalidCredentials(BusinessError):
  def __init__(self, detail: str = "Invalid credentials"):
    self.detail = detail
    super().__init__(self.detail)

class InvalidToken(BusinessError):
  def __init__(self, detail: str = "Invalid token"):
    self.detail = detail
    super().__init__(self.detail)

class InvalidTokenType(BusinessError):
  def __init__(self, detail: str = "Invalid token type"):
    self.detail = detail
    super().__init__(self.detail)

class InvalidTokenPayload(BusinessError):
  def __init__(self, detail: str = "Invalid token payload"):
    self.detail = detail
    super().__init__(self.detail)

class UserDisabled(BusinessError):
  def __init__(self, detail: str = "User account is disabled"):
    self.detail = detail
    super().__init__(self.detail)

class AuthProviderUnknown(BusinessError):
  def __init__(self, detail: str = "Unknown provider"):
    self.detail = detail
    super().__init__(self.detail)

class MissingIdToken(BusinessError):
  def __init__(self, detail: str = "Missing id_token"):
    self.detail = detail
    super().__init__(self.detail)

class InvalidAuth0Token(BusinessError):
  def __init__(self, detail: str = "Invalid Auth0 token"):
    self.detail = detail
    super().__init__(self.detail)

class EmailNotVerified(BusinessError):
  def __init__(self, detail: str = "Email not verified"):
    self.detail = detail
    super().__init__(self.detail)

class EmailNotFoundInToken(BusinessError):
  def __init__(self, detail: str = "Email not found in token"):
    self.detail = detail
    super().__init__(self.detail)

# =======================
# Company
# =======================

class CompanyNotFound(BusinessError):
  def __init__(self, detail: str = "Company not found"):
    self.detail = detail
    super().__init__(self.detail)

class CompanyForbidden(BusinessError):
  def __init__(self, detail: str = "Not enough permissions to access this company"):
    self.detail = detail
    super().__init__(self.detail)

class CompanyUpdateForbidden(BusinessError):
  def __init__(self, detail: str = "Only owner can update company"):
    self.detail = detail
    super().__init__(self.detail)

class CompanyDeleteForbidden(BusinessError):
  def __init__(self, detail: str = "Only owner can delete company"):
    self.detail = detail
    super().__init__(self.detail)

# =======================
# Company members
# =======================

class CompanyOwnerOnly(BusinessError):
  def __init__(self, detail: str = "Only owners can perform this action"):
    self.detail = detail
    super().__init__(self.detail)


class CompanyMembershipForbidden(BusinessError):
  def __init__(self, detail: str = "You are not allowed to perform this membership action"):
    self.detail = detail
    super().__init__(self.detail)

# =======================
# Company invitation
# =======================

class InvitationNotFound(BusinessError):
  def __init__(self, detail="Invitation not found"):
    self.detail = detail
    super().__init__(self.detail)

class InvitationAlreadyProcessed(BusinessError):
  def __init__(self, detail="Invitation already processed"):
    self.detail = detail
    super().__init__(self.detail)

class InvitationForbidden(BusinessError):
  def __init__(self, detail="Action not allowed for this invitation"):
    self.detail = detail
    super().__init__(self.detail)

# =======================
# Quizzes
# =======================
class BusinessError(Exception):
  def __init__(self, detail: str):
    self.detail = detail
    super().__init__(detail)
