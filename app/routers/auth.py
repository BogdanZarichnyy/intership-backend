from fastapi import APIRouter, Depends, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.core.dependencies import get_current_user, get_auth_service
from app.core.exceptions import AuthProviderUnknown
from app.schemas.user import SignInRequest, UserSchema
from app.services.auth import AuthService

router = APIRouter(tags=["auth"])
security = HTTPBearer()

# =========================
# Авторизація
# =========================
@router.post(
  "/login", 
  status_code=status.HTTP_200_OK
)
async def login(
  data: SignInRequest, 
  service: AuthService = Depends(get_auth_service)
):
  return await service.login(data.email, data.password)

# =========================
# Logout
# =========================
@router.post(
  "/logout", 
  status_code=status.HTTP_200_OK
)
async def logout(
  current_user: UserSchema = Depends(get_current_user)
):
  """
  - local: повертаємо повідомлення
  - auth0: редірект на Auth0 logout URL
  """
  if current_user.provider == "local":
    return JSONResponse({"message": "Logged out successfully (local user)"})
  elif current_user.provider == "auth0":
    logout_url = (
      f"https://{settings.auth0_domain}/v2/logout?"
      f"client_id={settings.auth0_client_id}&returnTo={settings.frontend_redirect_url}"
    )
    return RedirectResponse(url=logout_url)
  else:
    raise AuthProviderUnknown()

@router.post(
  "/refresh", 
  status_code=status.HTTP_200_OK
)
async def refresh_token(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  service: AuthService = Depends(get_auth_service),
):
  return await service.refresh_access_token(credentials.credentials)

@router.post(
  "/callback", 
  status_code=status.HTTP_200_OK
)
async def auth0_callback(
  data: dict = Body(...),
  service: AuthService = Depends(get_auth_service),
):
  id_token = data.get("id_token")
  return await service.handle_auth0_callback(id_token)
