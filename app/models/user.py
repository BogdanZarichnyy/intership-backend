import uuid
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.postgres import Base

class User(Base):
  __tablename__ = "users"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
    index=True
  )

  email: Mapped[str] = mapped_column(
    String(255),
    unique=True,
    nullable=False,
    index=True
  )

  username: Mapped[str] = mapped_column(
    String(100),
    unique=True,
    nullable=False
  )

  hashed_password: Mapped[str | None] = mapped_column(
    String(255),
    nullable=True  # users від провайдера Auth0 не мають password при авторизації, тому дозволяємо nullable=True, в подальшому його можна встановити
  )

  # Providers (наприклад local, auth0, google, github, etc) - параметр для розмежування користувачів, які реєструються або локально, або через різні провайдери
  provider: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    default="local",
    index=True
  )

  # Provider user id (наприклад auth0_id, github_id, google_id, etc) - унікальний ідентифікатор користувача від провайдера, який допомагає зв'язати локального користувача з його обліковим записом у провайдера
  provider_id: Mapped[str | None] = mapped_column(
    String(255),
    unique=True,
    nullable=True,
    index=True
  )

  is_active: Mapped[bool] = mapped_column(
    Boolean,
    default=True
  )

  created_at: Mapped[DateTime] = mapped_column(
    DateTime,
    server_default=func.now()
  )

  updated_at: Mapped[DateTime] = mapped_column(
    DateTime,
    server_default=func.now(),
    onupdate=func.now()
  )
