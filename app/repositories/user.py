from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from app.models.user import User

class UserRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def get_all_user(
    self,
    limit: int = 100,
    offset: int = 0
  ) -> list[User]:
    query = (
      select(User)
      .order_by(User.id)
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  async def count_users(
    self
  ) -> int:
    query = select(func.count()).select_from(User)
    result = await self.db.execute(query)
    return result.scalar_one()

  async def get_user_by_id(
    self,
    user_id: UUID
  ) -> User | None:
    query = select(User).where(User.id == user_id)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def get_user_by_email(
    self,
    email: str
  ) -> User | None:
    query = select(User).where(User.email == email)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()
  
  async def get_user_by_username(
    self,
    username: str
  ) -> User | None:
    query = select(User).where(User.username == username)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def get_user_by_provider_id(
    self,
    provider_id: str
  ) -> User | None:
    query = select(User).where(User.provider_id == provider_id)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def create_user(
    self,
    data: dict
  ) -> User:
    query = (
      insert(User)
      .values(**data)
      .returning(User)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one()

  async def update_user_details(
    self,
    user_id: UUID,
    new_data: dict
  ) -> User:
    query = (
      update(User)
      .where(User.id == user_id)
      .values(**new_data)
      .execution_options(synchronize_session="fetch")
      .returning(User)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one_or_none()

  async def delete_user(
    self,
    user_id: UUID
  ) -> None:
    query = delete(User).where(User.id == user_id)
    await self.db.execute(query)
    await self.db.commit()
