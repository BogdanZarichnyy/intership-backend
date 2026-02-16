from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import (
  UserSchema,
  SignInRequest,
  SignUpRequest,
  UserUpdate,
  UsersListResponse,
  UserDetailResponse
)
from app.models.user import User
from app.db.postgres import get_db

router = APIRouter(prefix="/users", tags=["users"])
