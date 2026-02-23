from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  host: str = "0.0.0.0"
  port: int = 8000

  cors_origins: list[str] = ["http://localhost:3000"]
  
  # Start DB
  max_retries: int = 5  # кількість спроб підключення до БД
  retry_delay: int = 2  # секунди
  
  # PostgreSQL
  postgres_host: str = "postgres"
  postgres_port: int = 5432
  postgres_user: str = "postgres"
  postgres_password: str = "postgres"
  postgres_db: str = "internship"

  # Redis
  redis_host: str = "redis"
  redis_port: int = 6379

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
