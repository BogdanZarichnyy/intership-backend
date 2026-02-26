from uuid import UUID
from app.models.user import User
from app.schemas.user import (
  UserSchema,
  SignUpRequest,
  UserUpdate,
  UsersListResponse,
  UserDetailResponse
)
from app.core.security import hash_password, verify_password
from app.core.logger import logger
from app.repositories.user import UserRepository
from app.core.exceptions import (
  ExistsEmail,
  InvalidPassword,
  MissingCurrentPassword,
)

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
    return UsersListResponse(
      users=[
        UserSchema.model_validate(user)
        for user in users
      ],
      total=total
    )

  async def get_user_by_id(
    self,
    user_id: UUID
  ) -> User | None:
    user = await self.repo.get_user_by_id(user_id)
    if user:
      logger.info(f"Fetched user id={user_id}")
    return user

  async def get_user_by_email(
    self,
    email: str
  ) -> User | None:
    return await self.repo.get_user_by_email(email)

  async def get_user_by_provider_id(
    self,
    provider_id: str
  ) -> User | None:
    return await self.repo.get_user_by_provider_id(provider_id)

  async def create_new_user(
      self,
      user_data: SignUpRequest
  ) -> UserDetailResponse:
    existing_user = await self.repo.get_user_by_email(
      user_data.email
    )
    if existing_user:
      logger.warning(
        f"User creation failed. Email exists: {user_data.email}"
      )
      raise ExistsEmail(user_data.email)
    hashed_password = (
      hash_password(user_data.password)
      if user_data.password
      else None
    )
    user = User(
      email=user_data.email,
      username=user_data.username,
      hashed_password=hashed_password,
      provider=user_data.provider or "local",
      provider_id=user_data.provider_id
    )
    user = await self.repo.create_user(user)
    logger.info(f"User created id={user.id}")
    return UserDetailResponse.model_validate(user)

  async def update_user_details(
    self,
    user: User,
    update_data: UserUpdate
  ) -> UserDetailResponse:
    if update_data.username is not None:
      user.username = update_data.username
    if update_data.new_password:
      if not update_data.current_password:
        raise MissingCurrentPassword()
      if not verify_password(
        update_data.current_password,
        user.hashed_password
      ):
        raise InvalidPassword()
      user.hashed_password = hash_password(
        update_data.new_password
      )
    user = await self.repo.update_user_details(user)
    logger.info(f"User updated id={user.id}")
    return UserDetailResponse.model_validate(user)

  async def delete_user(
    self,
    user: User
  ) -> None:
    await self.repo.delete_user(user)
    logger.info(f"User deleted id={user.id}")
