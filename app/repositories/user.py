from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User

class UserRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def get_all_user(
    self,
    limit: int,
    offset: int
  ) -> list[User]:
    result = await self.db.execute(
      select(User)
      .limit(limit)
      .offset(offset)
      .order_by(User.id)
    )
    return result.scalars().all()

  async def count(self) -> int:
    result = await self.db.execute(
      select(func.count()).select_from(User)
    )
    return result.scalar_one()

  async def get_user_by_id(
    self,
    user_id: UUID
  ) -> User | None:
    result = await self.db.execute(
      select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

  async def get_user_by_email(
    self,
    email: str
  ) -> User | None:
    result = await self.db.execute(
      select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
  
  async def get_user_by_username(
    self,
    username: str
  ) -> User | None:
    result = await self.db.execute(
      select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()

  async def get_user_by_provider_id(
    self,
    provider_id: str
  ) -> User | None:
    result = await self.db.execute(
      select(User).where(User.provider_id == provider_id)
    )
    return result.scalar_one_or_none()

  async def create_user(
    self,
    user: User
  ) -> User:
    self.db.add(user)
    await self.db.commit()
    await self.db.refresh(user)
    return user

  async def update_user_details(
    self,
    user: User
  ) -> User:
    await self.db.commit()
    await self.db.refresh(user)
    return user

  async def delete_user(
    self,
    user: User
  ) -> None:
    await self.db.delete(user)
    await self.db.commit()
