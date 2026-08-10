from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    #safe store .env variables
    DATABASE_URL: str
    REDIS_URL: str
    
    # JWT
    SECRET_KEY: str = "default_secret_key_for_dev_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # معادل ۲۴ ساعت

    # read .env variables
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# ساخت یک نمونه یکتا از تنظیمات
settings = Settings()