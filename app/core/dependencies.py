from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.log_context import current_user_id_var
from app.db.postgres import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company_invitation import CompanyInvitationRepository
from app.repositories.quiz import QuizRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.company import CompanyService
from app.services.company_member import CompanyMemberService
from app.services.company_invitation import CompanyInvitationService
from app.services.company_role import CompanyAdminService
from app.services.quiz import QuizService

security = HTTPBearer()

# UserService dependency
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
  return UserService(UserRepository(db))

# AuthService dependency
async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
  return AuthService(UserRepository(db))

# CompanyService dependency
async def get_company_service(db: AsyncSession = Depends(get_db)) -> CompanyService:
  return CompanyService(CompanyRepository(db))

# CompanyMemberService dependency
async def get_company_member_service(db: AsyncSession = Depends(get_db)) -> CompanyMemberService:
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  return CompanyMemberService(member_repo, company_repo)

# CompanyInvitationService dependency
async def get_invitation_service(db: AsyncSession = Depends(get_db)) -> CompanyInvitationService:
  invitation_repo = CompanyInvitationRepository(db)
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  return CompanyInvitationService(invitation_repo, member_repo, company_repo)

# CompanyAdminService dependency
async def get_company_admin_service(db: AsyncSession = Depends(get_db)) -> CompanyAdminService:
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  return CompanyAdminService(member_repo, company_repo)

# QuizService dependency
async def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
  quiz_repo = QuizRepository(db)
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  company_member_service = CompanyMemberService(member_repo, company_repo)
  return QuizService(quiz_repo, member_repo, company_repo, company_member_service)

# Поточний користувач із токена
async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  service: AuthService = Depends(get_auth_service),
)-> User:
  user = await service.get_current_user_from_token(credentials.credentials)
  current_user_id_var.set(str(user.id))  # ← додаємо це для логування, щоб бачити хто авторизований
  return user
