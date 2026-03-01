from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
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

__all__ = ["UserService"] # Для тестування

router = APIRouter(tags=["users"])

def get_user_service(
  db: AsyncSession = Depends(get_db)
) -> UserService:
  repo = UserRepository(db)
  return UserService(repo)

@router.get(
  "/",
  response_model=UsersListResponse, 
  status_code=status.HTTP_200_OK
)
async def get_all_users(
  limit: int = Query(10, ge=1, le=100),
  offset: int = Query(0, ge=0),
  service: UserService = Depends(get_user_service)
):
  return await service.get_all_users(limit, offset)

@router.get(
  "/{user_id}",
  response_model=UserDetailResponse, 
  status_code=status.HTTP_200_OK
)
async def get_user_by_id(
  user_id: UUID,
  service: UserService = Depends(get_user_service)
):
  return await service.get_user_by_id(user_id)

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

@router.patch(
  "/{user_id}",
  response_model=UserDetailResponse, 
  status_code=status.HTTP_200_OK
)
async def update_user(
  user_id: UUID,
  update_data: UserUpdate,
  service: UserService = Depends(get_user_service)
):
  user_model = await service.get_user_by_id(user_id)
  return await service.update_user_details(user_model, update_data)

@router.delete(
  "/{user_id}", 
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
  user_id: UUID,
  service: UserService = Depends(get_user_service)
):
  user_model = await service.get_user_by_id(user_id)
  await service.delete_user(user_model)
  return
