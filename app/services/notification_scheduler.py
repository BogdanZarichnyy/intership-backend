from uuid import UUID
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import DefaultDict
from app.models.company_member import CompanyMember
from app.models.quiz import Quiz
from app.models.quiz_workflow import QuizWorkflow
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.repositories.notification import NotificationRepository

class QuizReminderService:
  def __init__(
    self, 
    member_repo: CompanyMemberRepository,
    quiz_repo: QuizRepository,
    quiz_workflow_repo: QuizWorkflowRepository,
    notification_repo: NotificationRepository,
  ):
    self.member_repo = member_repo
    self.quiz_repo = quiz_repo
    self.quiz_workflow_repo = quiz_workflow_repo
    self.notification_repo = notification_repo

  @staticmethod
  def to_utc(dt):
    if dt is None:
      return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

  async def run_daily_reminder(
    self
  ) -> None:
    # Беремо всі компанії через унікальні company_id з членів
    all_members_result: list[CompanyMember] = await self.member_repo.get_all_members_for_notifications_for_all_companies()
    company_ids: list[UUID] = {member.company_id for member in all_members_result}

    now = datetime.now(timezone.utc)

    notifications = []

    for company_id in company_ids:

      members: list[CompanyMember] = await self.member_repo.get_all_members_for_notifications(company_id)
      quizzes: list[Quiz] = await self.quiz_repo.get_quizzes_of_company_for_notifications(company_id)
      workflows: list[QuizWorkflow] = await self.quiz_workflow_repo.get_company_workflows(company_id)

      # --- групування workflow по user ---
      user_workflows: DefaultDict[UUID, list[QuizWorkflow]] = defaultdict(list)
      for workflow in workflows:
        user_workflows[workflow.user_id].append(workflow)

      all_quiz_ids = {quiz.id for quiz in quizzes}

      for member in members:
        user_id = member.member_id
        user_wf = user_workflows.get(user_id, [])

        # --- якщо користувач нічого не проходив ---
        if not user_wf:
          for quiz in quizzes:
            notifications.append({
              "user_id": user_id,
              "quiz_id": quiz.id,
              "message": f"Будь ласка, пройдіть вікторину: {quiz.title}",
              "is_read": False
            })
          continue

        # --- останній пройдений квіз ---
        last_completed_at = max(self.to_utc(workflow.created_at) for workflow in user_wf)

        # --- ще не пройшло 24h ---
        if now < last_completed_at + timedelta(hours=24):
          continue

        completed_ids = {workflow.quiz_id for workflow in user_wf}
        pending_ids = all_quiz_ids - completed_ids

        # --- непройдені ---
        for quiz in quizzes:
          if quiz.id in pending_ids:
            notifications.append({
              "user_id": user_id,
              "quiz_id": quiz.id,
              "message": f"Будь ласка, пройдіть вікторину: {quiz.title}",
              "is_read": False
            })

        # # --- пройдені (закриваємо notification) --- це для створення записів для старих завершених квізів
        # for quiz in quizzes:
        #   if quiz.id in completed_ids:
        #     notifications.append({
        #       "user_id": user_id,
        #       "quiz_id": quiz.id,
        #       "message": f"Вікторину пройдено: {quiz.title}",
        #       "is_read": True
        #     })

      if notifications:
        await self.notification_repo.upsert_notifications(notifications)
