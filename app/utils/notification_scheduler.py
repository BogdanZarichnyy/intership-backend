from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import SessionLocal
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.repositories.notification import NotificationRepository
from app.services.notification_scheduler import QuizReminderService

async def job():
  async with SessionLocal() as db:
    # Ініціалізація репозиторіїв
    member_repo = CompanyMemberRepository(db)
    quiz_repo = QuizRepository(db)
    quiz_workflow_repo = QuizWorkflowRepository(db)
    notification_repo = NotificationRepository(db)

    service = QuizReminderService(member_repo, quiz_repo, quiz_workflow_repo, notification_repo)
    await service.run_daily_reminder()

def start_scheduler(hour: int = 0, minute: int = 0):
  scheduler = AsyncIOScheduler()
  scheduler.add_job(job, 'cron', hour=hour, minute=minute)
  scheduler.start()
  print(f"Scheduler started, next run at {hour:02}:{minute:02}")
