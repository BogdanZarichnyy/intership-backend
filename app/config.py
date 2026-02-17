from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  host: str = "0.0.0.0"
  port: int = 8000

  cors_origins: list[str] = ["http://localhost:3000"]
  
  # PostgreSQL
  postgres_host: str = "postgres"
  postgres_port: int = 5432
  postgres_user: str = "postgres"
  postgres_password: str = "postgres"
  postgres_db: str = "internship"

  # Redis
  redis_host: str = "redis"
  redis_port: int = 6379

  # JWT (ДОДАЙ ЦЕ)
  secret_key: str
  algorithm: str = "HS256"
  access_token_expire_minutes: int = 30  # Час життя access токена в хвилинах
  refresh_token_expire_days: int = 7  # Час життя refresh токена в днях

  # Auth0
  auth0_domain: str
  auth0_audience: str
  auth0_client_id: str
  auth0_client_secret: str
  auth0_secret: str
  auth0_redirect_uri: str

  model_config = SettingsConfigDict(
    env_file=".env",
    env_prefix=""
  )

  @property
  def database_url(self) -> str:
    return (
      f"postgresql+asyncpg://"
      f"{self.postgres_user}:{self.postgres_password}"
      f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    )

  @property
  def redis_url(self) -> str:
    return f"redis://{self.redis_host}:{self.redis_port}"

settings = Settings()
