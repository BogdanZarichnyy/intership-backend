from uuid import UUID
from datetime import datetime
from sqlalchemy import select, case, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.quiz_workflow import QuizWorkflow
from app.models.quiz import Quiz

class AnalyticsRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  # =============================
  # User-specific analytics
  # =============================

  # Загальний рейтинг користувача - середній бал за всі квізи
  async def get_user_overall_rating_repo(
    self, 
    user_id: UUID
  ):
    stmt = select(func.avg(QuizWorkflow.score)).where(
      QuizWorkflow.user_id == user_id
    )
    result = await self.db.execute(stmt)
    return result.scalar()

  # Список середніх балів для кожного квізу, 
  # пройденого користувачем, з часовими діапазонами
  async def get_user_average_scores_repo(
    self, 
    user_id: UUID, 
  ):
    stmt = (
      select(
        Quiz.id,
        Quiz.title,
        func.avg(QuizWorkflow.score).label("average_score"),
        func.max(QuizWorkflow.updated_at).label("last_attempt")
      )
      .join(Quiz, Quiz.id == QuizWorkflow.quiz_id)
      .where(
        QuizWorkflow.user_id == user_id,
      )
      .group_by(Quiz.id, Quiz.title)
    )
    result = await self.db.execute(stmt)
    rows = result.mappings().all()  # <-- повертає список словників
    return [
      {
        "id": row["id"], 
        "title": row["title"], 
        "average_score": round(float(row["average_score"] or 0.0), 2),
        "last_attempt": row["last_attempt"]
      }
      for row in rows
    ]

  # Список тестів разом з часовими позначками їх останнього виконання
  async def get_user_quizzes_with_timestamps(
    self, 
  ):
    stmt = (
      select(
        Quiz.id,
        Quiz.title,
        case(
          (Quiz.participation_count > 0, Quiz.updated_at),  # якщо є хоча б одна участь у квізі, тоді повертаємо дату з поля updated_at
          else_=None                                        # якщо участі немає, тоді повертаємо null
        ).label("updated_at")
      )
      .group_by(Quiz.id, Quiz.title, Quiz.updated_at, Quiz.participation_count)
    )
    result = await self.db.execute(stmt)
    rows = result.mappings().all()  # <-- повертає список словників
    return [
      {
        "id": row["id"], 
        "title": row["title"], 
        "updated_at": row["updated_at"]
      }
      for row in rows
    ]

  # =============================
  # Company-specific analytics
  # =============================

  # Список середніх балів всіх членів компанії з часовими діапазонами
  async def get_company_members_scores(
    self, 
    company_id: UUID, 
    start_date: datetime,
    end_date: datetime
  ):
    # Повертає середній бал кожного члена компанії за вказаний період
    stmt = (
      select(
        User.id,
        User.username,
        func.avg(QuizWorkflow.score).label("average_score"),
        func.max(QuizWorkflow.updated_at).label("last_attempt")  # останнє оновлення
      )
      .join(QuizWorkflow, QuizWorkflow.user_id == User.id)
      .join(CompanyMember, CompanyMember.member_id == User.id)
      .where(
        CompanyMember.company_id == company_id,
        QuizWorkflow.company_id == company_id,
        QuizWorkflow.updated_at >= start_date,
        QuizWorkflow.updated_at <= end_date
      )
      .group_by(User.id, User.username)
    )
    result = await self.db.execute(stmt)
    rows = result.mappings().all()
    # Перетворюємо у список чистих словників з Python-типами
    return [
      {
        "id": row["id"],
        "username": row["username"],
        "average_score": round(float(row["average_score"] or 0.0), 2),
        "last_attempt": row["last_attempt"]
      }
      for row in rows
    ]

  # Список середніх балів для кожного тесту, пройденого вибраним користувачем з часовими діапазонами
  async def get_company_average_scores_quizzes(
    self, 
    company_id: UUID,
    user_id: UUID, 
    start_date: datetime,
    end_date: datetime
  ):
    # Детальна статистика користувача по кожному квізу
    stmt = (
      select(
        Quiz.id.label("quiz_id"),
        Quiz.title,
        User.id.label("user_id"),
        User.username,
        func.avg(QuizWorkflow.score).label("average_score"),
        func.max(QuizWorkflow.updated_at).label("last_attempt")
      )
      .join(Quiz, Quiz.id == QuizWorkflow.quiz_id)
      .join(User, User.id == QuizWorkflow.user_id)
      .where(
        QuizWorkflow.company_id == company_id,
        QuizWorkflow.user_id == user_id,
        QuizWorkflow.updated_at >= start_date,
        QuizWorkflow.updated_at <= end_date
      )
      .group_by(Quiz.id, Quiz.title, User.id, User.username)
    )
    result = await self.db.execute(stmt)
    rows = result.mappings().all()
    # Перетворюємо у список чистих словників з Python-типами
    if not rows:
      return {}
    user_info = {
      "user_id": rows[0]["user_id"],    # Беремо дані користувача з першого рядка
      "username": rows[0]["username"],  # Беремо дані користувача з першого рядка
      "average_scores_quizzes": [
        {
          "quiz_id": row["quiz_id"],
          "title": row["title"],
          "average_score": round(float(row["average_score"] or 0.0), 2),
          "last_attempt": row["last_attempt"]
        }
        for row in rows
      ]
    }
    return user_info

  async def get_company_members_last_attempts(
    self, 
    company_id: UUID
  ):
    # Отримуємо інформацію про компанію
    company_stmt = select(
      Company.id,
      Company.name,
      Company.description
    ).where(Company.id == company_id)
    company_result = await self.db.execute(company_stmt)
    company = company_result.mappings().first()
    if not company:
      return {
        "id": None,
        "name": "",
        "description": "",
        "list_company_members": []
      }
    # Отримуємо останні спроби членів компанії
    members_stmt = (
      select(
        User.id.label("user_id"),
        User.username,
        func.max(QuizWorkflow.updated_at).label("last_attempt")
      )
      .join(QuizWorkflow, QuizWorkflow.user_id == User.id)
      .join(CompanyMember, CompanyMember.member_id == User.id)
      .where(CompanyMember.company_id == company_id)
      .group_by(User.id, User.username)
    )
    members_result = await self.db.execute(members_stmt)
    members_rows = members_result.mappings().all()  # список словників
    return {
      "id": company["id"],
      "name": company["name"],
      "description": company["description"],
      "list_company_members": [
        {
          "user_id": row["user_id"],
          "username": row["username"],
          "updated_at": row["last_attempt"]
        }
        for row in members_rows
      ]
    }
