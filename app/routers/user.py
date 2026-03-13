from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, get_user_service
from app.models.user import User
from app.schemas.user import (
  UserSchema,
  SignUpRequest,
  UsersListResponse,
  UserUpdate
)
from app.services.user import UserService

router = APIRouter(tags=["users"])

@router.get(
  "/me",
  response_model=UserSchema,
  status_code=status.HTTP_200_OK
)
async def get_me(
  current_user: User = Depends(get_current_user)
):
  """Повертає дані поточного користувача на основі access token."""
  return current_user

@router.get(
  "/",
  response_model=UsersListResponse,
  status_code=status.HTTP_200_OK
)
async def get_all_users(
  limit: int = Query(10, ge=1, le=100),
  offset: int = Query(0, ge=0),
  current_user: User = Depends(get_current_user),
  service: UserService = Depends(get_user_service)
):
  return await service.get_all_users(limit, offset)

@router.get(
  "/{user_id}",
  response_model=UserSchema,
  status_code=status.HTTP_200_OK
)
async def get_user_by_id(
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: UserService = Depends(get_user_service)
):
  return await service.get_user_by_id(user_id)

@router.post(
  "/",
  response_model=UserSchema,
  status_code=status.HTTP_201_CREATED
)
async def create_new_user(
  user_data: SignUpRequest,
  service: UserService = Depends(get_user_service)
):
  return await service.create_new_user(user_data)

@router.patch(
  "/{user_id}",
  response_model=UserSchema,
  status_code=status.HTTP_200_OK
)
async def update_user(
  user_id: UUID,
  update_data: UserUpdate,
  current_user: User = Depends(get_current_user),
  service: UserService = Depends(get_user_service)
):
  return await service.update_user_details(user_id, update_data, current_user)

@router.delete(
  "/{user_id}",
  response_model=None,
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: UserService = Depends(get_user_service)
):
  await service.delete_user(user_id, current_user)
