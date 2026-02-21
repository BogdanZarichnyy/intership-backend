from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import (
  SignUpRequest,
  UserUpdate,
  UsersListResponse,
  UserDetailResponse
)
from app.db.postgres import get_db
from app.services.user import UserService
from app.core.dependencies import get_current_user
from app.core.security import (
  verify_password
)

__all__ = ["UserService"] # Для тестування

router = APIRouter(tags=["users"])

def get_user_service(
  db: AsyncSession = Depends(get_db)
) -> UserService:
  return UserService(db)

@router.get(
  "/me",
  response_model=UserDetailResponse,
  summary="Current User Info",
)
async def get_me(
    current_user: UserDetailResponse = Depends(get_current_user)  # додамо авторизацію щоб тільки авторизовані могли отримувати дані користувачів
  ):
  """Повертає дані поточного користувача на основі access token."""
  return current_user

@router.get(
  "/",
  response_model=UsersListResponse
)
async def get_all_users(
  limit: int = Query(10, ge=1, le=100),
  offset: int = Query(0, ge=0),
  current_user: UserDetailResponse = Depends(get_current_user),  # додамо авторизацію щоб тільки авторизовані могли отримувати дані користувачів
  service: UserService = Depends(get_user_service)
):
  return await service.get_all_users(limit, offset)

@router.get(
  "/{user_id}",
  response_model=UserDetailResponse
)
async def get_user_by_id(
  user_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),  # додамо авторизацію щоб тільки авторизовані могли отримувати дані користувачів
  service: UserService = Depends(get_user_service)
):
  user = await service.get_user_by_id(user_id)
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  return user

@router.post(
  "/",
  response_model=UserDetailResponse,
  status_code=status.HTTP_201_CREATED
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
  current_user: UserDetailResponse = Depends(get_current_user),  # додамо авторизацію щоб тільки авторизовані могли отримувати дані користувачів
  service: UserService = Depends(get_user_service)
):
  # Переконуємося, що користувач змінює тільки себе
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to update this user"
    )
  # Витягуємо ORM-модель користувача, щоб мати можливість оновлювати її
  user_model = await service.get_user_by_id(user_id)
  if not user_model:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  # Перевірка поточного пароля при зміні пароля
  if update_data.new_password:
    if not update_data.current_password:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Current password must be provided to set a new password"
      )
    if not verify_password(update_data.current_password, user_model.hashed_password):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Current password is incorrect"
      )
  # Фінальне оновлення в БД через сервіс
  updated_user = await service.update_user_details(user_model, update_data)
  return updated_user  # FastAPI автоматично конвертує у UserDetailResponse

@router.delete(
  "/{user_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
  user_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),  # додамо авторизацію щоб тільки авторизовані могли отримувати дані користувачів
  service: UserService = Depends(get_user_service)
):
  # Користувач може змінювати тільки свої дані
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to delete this user"
    )
  user_model = await service.get_user_by_id(user_id)
  if not user_model:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  deleted_user = await service.delete_user(user_model)
  return deleted_user
