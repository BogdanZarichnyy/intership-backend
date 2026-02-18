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
async def get_me(current_user = Depends(get_current_user)):
  """Повертає дані поточного користувача на основі access token."""
  return current_user

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
  user_id: int,
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
  user_id: int,
  update_data: UserUpdate,
  service: UserService = Depends(get_user_service)
):
  user_model = await service.get_user_by_id(user_id)
  if not user_model:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  return await service.update_user_details(
    user_model,
    update_data
  )

@router.delete(
  "/{user_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
  user_id: int,
  service: UserService = Depends(get_user_service)
):
  user_model = await service.get_user_by_id(user_id)
  if not user_model:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  await service.delete_user(user_model)
