from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from app.core.exceptions import InvalidToken
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
  return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
  return pwd_context.verify(password, hashed)

def create_access_token(data: dict) -> str:
  to_encode = data.copy()
  expire = datetime.now(timezone.utc) + timedelta(
    minutes=settings.access_token_expire_minutes
  )
  to_encode.update({
    "exp": expire,
    "type": "access"
  })
  return jwt.encode(
    to_encode,
    settings.jwt_secret_key,
    algorithm=settings.jwt_algorithm
  )

def create_refresh_token(data: dict) -> str:
  to_encode = data.copy()
  expire = datetime.now(timezone.utc) + timedelta(
    days=settings.refresh_token_expire_days
  )
  to_encode.update({
    "exp": expire,
    "type": "refresh"
  })
  return jwt.encode(
    to_encode,
    settings.jwt_secret_key,
    algorithm=settings.jwt_algorithm
  )

def decode_token(token: str) -> dict:
  try:
    payload = jwt.decode(
      token,
      settings.jwt_secret_key,
      algorithms=[settings.jwt_algorithm]
    )
    return payload
  except ExpiredSignatureError:
    raise InvalidToken("Token has expired")
  except JWTError:
    raise InvalidToken("Invalid token")
