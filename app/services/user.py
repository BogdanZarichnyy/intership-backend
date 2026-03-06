from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import (
  UserSchema,
  SignUpRequest,
  UserUpdate,
  UsersListResponse
)
from app.core.security import hash_password, verify_password
from app.repositories.user import UserRepository
from app.core.exceptions import (
  ForbiddenAction,
  UserNotFound,
  ExistsEmail,
  ExistsUsername,
  InvalidPassword,
  MissingCurrentPassword,
)
from app.core.logger import logger

class UserService:

  def __init__(self, repository: UserRepository):
    self.repo = repository

  async def get_all_users(
    self,
    limit: int = 10,
    offset: int = 0
  ) -> UsersListResponse:
    users = await self.repo.get_all_user(limit, offset)
    total = await self.repo.count()
    logger.info(f"Fetched users list limit={limit} offset={offset}")
    return UsersListResponse(users=[UserSchema.model_validate(user) for user in users], total=total)

  async def get_user_by_id(
    self,
    user_id: UUID
  ) -> User:
    user = await self.repo.get_user_by_id(user_id)
    if not user:
      raise UserNotFound()
    logger.info(f"Fetched user id={user_id}")
    return user

  async def get_user_by_email(
    self,
    email: str
  ) -> User:
    user = await self.repo.get_user_by_email(email)
    if not user:
      raise UserNotFound()
    logger.info(f"Fetched user email={email}")
    return user

  async def get_user_by_provider_id(
    self,
    provider_id: str
  ) -> User:
    user = await self.repo.get_user_by_provider_id(provider_id)
    if not user:
      raise UserNotFound()
    logger.info(f"Fetched user provider_id={provider_id}")
    return user

  async def create_new_user(
    self,
    user_data: SignUpRequest
  ) -> UserSchema:
    # Перевірка email
    existing_user = await self.repo.get_user_by_email(user_data.email)
    if existing_user:
      logger.warning(f"User creation failed. Email exists: {user_data.email}")
      raise ExistsEmail(user_data.email)
    # Перевірка username
    existing_user_by_username = await self.repo.get_user_by_username(user_data.username)
    if existing_user_by_username:
      logger.warning(f"User creation failed. Username exists: {user_data.username}")
      raise ExistsUsername(user_data.username)
    # Хешування пароля
    hashed_password = hash_password(user_data.password) if user_data.password else None
    user = User(
      email=user_data.email,
      username=user_data.username,
      hashed_password=hashed_password,
      provider=user_data.provider or "local",
      provider_id=user_data.provider_id
    )
    try:
      # Додаємо користувача у сесію та комітимо
      user = await self.repo.create_user(user)
    except IntegrityError as e:
      # Перевірка унікальних ключів на рівні БД
      if "users_username_key" in str(e.orig):
        logger.warning(f"User creation failed. Username exists: {user_data.username}")
        raise ExistsUsername(user_data.username)
      if "users_email_key" in str(e.orig):
        logger.warning(f"User creation failed. Email exists: {user_data.email}")
        raise ExistsEmail(user_data.email)
      raise
    logger.info(f"User created id={user.id}")
    return UserSchema.model_validate(user)

  async def update_user_details(
    self,
    user_id: UUID,
    update_data: UserUpdate,
    current_user_id: UUID
  ) -> UserSchema:
    # Переконуємося що користвуач змінює свої дані
    if user_id != current_user_id:
      raise ForbiddenAction("You are trying to edit data that is not yours")
    user = await self.repo.get_user_by_id(user_id)
    if not user:
      raise UserNotFound()
    logger.info(f"Fetched user id={user_id}")
    # --- Username ---
    if update_data.username is not None:
      # якщо username реально змінюється
      if update_data.username != user.username:
        existing_user = await self.repo.get_user_by_username(update_data.username)
        if existing_user:
          logger.warning(f"Username already exists: {update_data.username}")
          raise ExistsUsername(update_data.username)
        user.username = update_data.username
    # --- Password ---
    if update_data.new_password is not None:
      if update_data.current_password is None:
        logger.warning("Current password must be provided")
        raise MissingCurrentPassword()
      if not verify_password(
        update_data.current_password,
        user.hashed_password
      ):
        logger.warning("Current password is incorrect")
        raise InvalidPassword()
      user.hashed_password = hash_password(update_data.new_password)
    user = await self.repo.update_user_details(user)
    logger.info(f"User updated id={user.id}")
    return UserSchema.model_validate(user)

  async def delete_user(
    self,
    user_id: UUID,
    current_user: User
  ) -> None:
    # Переконуємося що користвуач змінює свої дані
    if user_id != current_user.id:
      raise ForbiddenAction("You are trying to edit data that is not yours")
    user = await self.repo.get_user_by_id(user_id)
    if not user:
      raise UserNotFound()
    logger.info(f"Fetched user id={user_id}")
    await self.repo.delete_user(user)
    logger.info(f"User deleted id={user_id}")
