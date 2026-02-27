from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import (
  SignUpRequest,
  UserUpdate,
  UsersListResponse,
  UserDetailResponse
)
from app.db.postgres import get_db
from app.services.user import UserService
from app.repositories.user import UserRepository
from app.core.exceptions import UserNotFound

__all__ = ["UserService"] # Для тестування

router = APIRouter(tags=["users"])

def get_user_service(
  db: AsyncSession = Depends(get_db)
) -> UserService:
  repo = UserRepository(db)
  return UserService(repo)

@router.get(
  "/",
  response_model=UsersListResponse
)
async def get_all_users(
  limit: int = Query(10, ge=1, le=100),
  offset: int = Query(0, ge=0),
  service: UserService = Depends(get_user_service)
):
  return await service.get_all_users(limit, offset)

@router.get(
  "/{user_id}",
  response_model=UserDetailResponse
)
async def get_user_by_id(
  user_id: UUID,
  service: UserService = Depends(get_user_service)
):
  user = await service.get_user_by_id(user_id)
  if not user:
    raise UserNotFound()
  return user

@router.post(
  "/",
  response_model=UserDetailResponse,
)
async def create_new_user(
  user_data: SignUpRequest,
  service: UserService = Depends(get_user_service)
):
  return await service.create_new_user(user_data)

@router.put(
  "/{user_id}",
  response_model=UserDetailResponse
)
async def update_user(
  user_id: UUID,
  update_data: UserUpdate,
  service: UserService = Depends(get_user_service)
):
  # Витягуємо ORM-модель користувача, щоб мати можливість оновлювати її
  user_model = await service.get_user_by_id(user_id)
  if not user_model:
    raise UserNotFound()
  # Відсилаємо дані в сервіс для подальшої перевірки
  updated_user = await service.update_user_details(user_model, update_data)
  return updated_user  # FastAPI автоматично конвертує у UserDetailResponse

@router.delete(
  "/{user_id}",
)
async def delete_user(
  user_id: UUID,
  service: UserService = Depends(get_user_service)
):
  user_model = await service.get_user_by_id(user_id)
  if not user_model:
    raise UserNotFound()
  await service.delete_user(user_model)
  return
