from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
  host: str = "0.0.0.0"
  port: int = 8000

  cors_origins: List[str] = ["http://localhost:3000"]

  model_config = SettingsConfigDict(
    env_file=".env",
    env_prefix=""
  )

settings = Settings()
