from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_
from app.models.notification import Notification
from itertools import islice

class NotificationRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_notifications_bulk(
    self, 
    notifications: list[dict],
    batch_size: int = 1000
  ) -> None:
    if not notifications:
      return None
    # Розбиваємо список на чанки - це зменшує ризик проблем з великим IN і підвищує ефективність на великих даних
    def chunks(list_dict, number):
      iteration = iter(list_dict)
      for first in iteration:
        yield [first] + list(islice(iteration, number - 1))
    for batch in chunks(notifications, batch_size):
      quiz_ids = {notification["quiz_id"] for notification in batch}
      user_ids = {notification["user_id"] for notification in batch}
      # Дістаємо існуючі записи тільки для цього чанка
      existing_result = await self.db.execute(
        select(Notification.user_id, Notification.quiz_id)
        .where(
          and_(
            Notification.quiz_id.in_(quiz_ids),
            Notification.user_id.in_(user_ids)
          )
        )
      )
      existing_pairs = set(existing_result.all())
      # Фільтруємо нові сповіщення і додаємо їх в базу
      new_notifications = [
        notification for notification in batch
        if (notification["user_id"], notification["quiz_id"]) not in existing_pairs
      ]
      if new_notifications:
        await self.db.execute(insert(Notification).values(new_notifications))
    await self.db.commit()

  async def get_user_notifications(
    self, 
    user_id: UUID
  ) -> list[Notification]:
    query = await self.db.execute(
      select(Notification)
      .where(Notification.user_id == user_id).
      order_by(Notification.created_at.desc())
    )
    return query.scalars().all()

  async def get_notification_by_id(
    self, 
    notification_id: UUID
  ) -> Notification:
    query = await self.db.execute(
      select(Notification).where(Notification.id == notification_id)
    )
    return query.scalar_one_or_none()

  async def mark_notification_as_read(
    self, 
    notification_id: UUID,
    current_user_id: UUID
  ) -> Notification:
    query = (
      update(Notification)
      .where(
        Notification.id == notification_id,
        Notification.user_id == current_user_id
      )
      .values(is_read=True)
      .returning(Notification)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one_or_none()
