from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, bindparam
from app.models.notification import Notification
from itertools import islice

class NotificationRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_notifications_bulk(
    self, 
    notifications: list[dict],
    chunk_size: int = 1000
  ) -> None:
    if not notifications:
      return None
    # Розбиваємо список на чанки - це зменшує ризик проблем з великим IN і підвищує ефективність на великих даних
    def chunks(list_dict, number):
      iteration = iter(list_dict)
      for first in iteration:
        yield [first] + list(islice(iteration, number - 1))
    for batch in chunks(notifications, chunk_size):
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
      .where(
        Notification.user_id == user_id,
        # Notification.is_read == False,
      )
      .order_by(Notification.updated_at.desc())
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

  async def update_notification_status(
    self, 
    notification_id: UUID,
    current_user_id: UUID,
    is_read: bool
  ) -> Notification:
    query = (
      update(Notification)
      .where(
        Notification.id == notification_id,
        Notification.user_id == current_user_id
      )
      .values(is_read=is_read)
      .returning(Notification)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one_or_none()

  async def reset_notifications_for_quiz(
    self,
    quiz_id: UUID
  ) -> None:
    query = (
      update(Notification)
      .where(Notification.quiz_id == quiz_id)
      .values(
        is_read=False
      )
    )
    await self.db.execute(query)
    await self.db.commit()

  async def upsert_notifications(
    self,
    notifications: list[dict],
    chunk_size: int = 1000
  ) -> None:
    if not notifications:
      return
    def chunks(list_dict, number):
      iterator = iter(list_dict)
      for first in iterator:
        yield [first] + list(islice(iterator, number - 1))
    for batch in chunks(notifications, chunk_size):
      quiz_ids = {n["quiz_id"] for n in batch}
      user_ids = {n["user_id"] for n in batch}
      existing_result = await self.db.execute(
        select(Notification)
        .where(
          and_(
            Notification.quiz_id.in_(quiz_ids),
            Notification.user_id.in_(user_ids)
          )
        )
      )
      existing = existing_result.scalars().all()
      existing_map = {
        (n.user_id, n.quiz_id): n
        for n in existing
      }
      to_insert = []
      to_update = []
      for n in batch:
        key = (n["user_id"], n["quiz_id"])
        if key in existing_map:
          to_update.append(n)
        else:
          to_insert.append(n)
      # INSERT нових
      if to_insert:
        await self.db.execute(insert(Notification).values(to_insert))
      # UPDATE існуючих
      for n in to_update:
        await self.db.execute(
          update(Notification)
          .where(
            Notification.user_id == n["user_id"],
            Notification.quiz_id == n["quiz_id"]
          )
          .values(
            message=n["message"],
            is_read=n["is_read"]
          )
        )
    await self.db.commit()
