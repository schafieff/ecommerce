from pathlib import Path
from pydantic_settings import SettingsConfigDict, BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DOTENV_FILE: Path = BASE_DIR / ".env"

   # The V2 way to configure behavior
    model_config = SettingsConfigDict(
        env_file=DOTENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Ignore extra environment variables not defined here
    )

# Single instance used everywhere
settings = Settings()