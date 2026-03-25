from uuid import UUID
from typing import IO
from app.core.logger import logger
from app.core.exceptions import CompanyNotFound
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.quiz import QuizRepository
from app.services.company_member import CompanyMemberService
from app.services.quiz import QuizService
from app.schemas.quiz import QuizCreateRequest, QuizUpdateRequest
from app.utils.quiz_excel_parser import parse_quiz_excel


class QuizImportService:
  def __init__(
    self,
    company_repo: CompanyRepository,
    company_member_service: CompanyMemberService,
    quiz_repo: QuizRepository,
    quiz_service: QuizService,
  ):
    self.company_repo = company_repo
    self.company_member_service = company_member_service
    self.quiz_repo = quiz_repo
    self.quiz_service = quiz_service

  async def import_excel(
    self,
    company_id: UUID,
    current_user: User,
    file: IO
  ) -> dict:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found company_id={company_id}")
      raise CompanyNotFound()
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    parsed_quizzes = parse_quiz_excel(file)
    for quiz_data in parsed_quizzes:
      existing = await self.quiz_repo.get_by_title_and_company(
        quiz_data["title"],
        company_id
      )
      if existing:
        await self.quiz_service.update_quiz(
          company_id,
          existing.id,
          current_user,
          QuizUpdateRequest(**quiz_data)
        )
      else:
        await self.quiz_service.create_quiz(
          company_id,
          current_user,
          QuizCreateRequest(**quiz_data)
        )
