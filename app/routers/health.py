from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
  status: str
  message: str

@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
  return HealthResponse(status="ok", message="working")
