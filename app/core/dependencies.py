from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.company import CompanyService
from app.services.company_member import CompanyMemberService
from app.services.company_invitation import CompanyInvitationService
from app.services.company_role import CompanyAdminService
from app.services.quiz import QuizService
from app.services.quiz_workflow import QuizWorkflowService

from app.core.log_context import current_user_id_var

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
  return CompanyInvitationService(db)

# CompanyAdminService dependency
async def get_company_admin_service(db: AsyncSession = Depends(get_db)) -> CompanyAdminService:
  return CompanyAdminService(db)

# QuizService dependency
async def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
  return QuizService(QuizRepository(db), CompanyMemberRepository(db))

# QuizWorkflowService dependency
def get_quiz_workflow_service(
  db: AsyncSession = Depends(get_db),
  quiz_service: QuizService = Depends(get_quiz_service)
) -> QuizWorkflowService:
  return QuizWorkflowService(QuizWorkflowRepository(db), quiz_service)

# Поточний користувач із токена
async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  service: AuthService = Depends(get_auth_service),
)-> User:
  user = await service.get_current_user_from_token(credentials.credentials)
  current_user_id_var.set(str(user.id))  # ← додаємо це для логування, щоб бачити хто авторизований
  return user
