from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import (
  UserSchema,
  SignUpRequest,
  UserUpdate,
  UsersListResponse,
  UserDetailResponse
)
from app.core.security import hash_password
import logging

logger = logging.getLogger("app")

class UserService:
  def __init__(self, db: AsyncSession):
    self.db = db

  # Отримуємо список користувачів з пагінацією
  async def get_all_users(
    self,
    limit: int = 10,
    offset: int = 0
  ) -> UsersListResponse:
    try:
      result = await self.db.execute(
        select(User)
        .limit(limit)
        .offset(offset)
        .order_by(User.id)
      )
      users = result.scalars().all()
      total_result = await self.db.execute(
        select(func.count()).select_from(User)
      )
      total = total_result.scalar_one()
      logger.info(
        f"Fetched users list limit={limit} offset={offset}"
      )
      return UsersListResponse(
        users=[
          UserSchema.model_validate(user)
          for user in users
        ],
        total=total
      )
    except Exception as e:
      logger.error(f"Failed to fetch users list: {e}")
      raise

  # Пошук користувача за ID
  async def get_user_by_id(
    self,
    user_id: UUID
  ) -> User | None:
    try:
      result = await self.db.execute(
        select(User).where(User.id == user_id)
      )
      user = result.scalar_one_or_none()
      if not user:
        return None
      logger.info(f"Fetched user id={user_id}")
      return user # повертаємо ORM-модель, а не Pydantic-схему, щоб мати можливість оновлювати її в інших методах
    except Exception as e:
      logger.error(
        f"Failed to fetch user id={user_id}: {e}"
      )
      raise

  # Пошук користувача за provider_id (для Auth0, Google, GitHub і т.д.)
  async def get_user_by_provider_id(self, provider_id: str) -> User | None:
    result = await self.db.execute(
      select(User).where(User.provider_id == provider_id)
    )
    return result.scalar_one_or_none()

  # Пошук користувача за email
  async def get_user_by_email(self, email: str) -> User | None:
    result = await self.db.execute(
      select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

  # Створення нового користувача
  async def create_new_user(
    self,
    user_data: SignUpRequest
  ) -> UserDetailResponse:
    try:
      # Перевірка чи існує користувач з таким E-mail
      result = await self.db.execute(
        select(User).where(User.email == user_data.email)
      )
      existing_user = result.scalar_one_or_none()
      if existing_user:
        logger.warning(
          f"User creation failed. Email already exists: {user_data.email}"
        )
        raise HTTPException(
          status_code=status.HTTP_409_CONFLICT,
          detail={
            "message": "User with this email already exists",
            "email": user_data.email
          }
        )
      # Хешуємо пароль лише якщо він є
      hashed_password = hash_password(user_data.password) if user_data.password else None
      # Створюємо нового користувача в БД
      user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        provider=user_data.provider or "local", # За замовчуванням "local" згідно моделі, якщо не вказаний інший провайдер
        provider_id=user_data.provider_id
      )
      self.db.add(user)
      await self.db.commit()
      await self.db.refresh(user)
      logger.info(
        f"User created id={user.id}"
      )
      return UserDetailResponse.model_validate(user)
    except Exception as e:
      await self.db.rollback()
      logger.error(
        f"Failed to create user email={user_data.email}: {e}"
      )
      raise

  # Оновлення деталей користувача
  async def update_user_details(
    self,
    user: User,
    update_data: UserUpdate
  ) -> UserDetailResponse:
    try:
      if update_data.email is not None:
        user.email = update_data.email
      if update_data.username is not None:
        user.username = update_data.username
      if update_data.is_active is not None:
        user.is_active = update_data.is_active
      if update_data.new_password:
        user.hashed_password = hash_password(
          update_data.new_password
        )
      await self.db.commit()
      await self.db.refresh(user)
      logger.info(
        f"User updated id={user.id}"
      )
      return UserDetailResponse.model_validate(user)
    except Exception as e:
      await self.db.rollback()
      logger.error(
        f"Failed to update user id={user.id}: {e}"
      )
      raise

  # Видалення існуючого користувача
  async def delete_user(
    self,
    user: User
  ) -> None:
    try:
      await self.db.delete(user)
      await self.db.commit()
      logger.info(
        f"User deleted id={user.id}"
      )
    except Exception as e:
      await self.db.rollback()
      logger.error(
        f"Failed to delete user id={user.id}: {e}"
      )
      raise
