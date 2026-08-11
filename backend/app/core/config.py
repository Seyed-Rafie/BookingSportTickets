from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    #safe store .env variables
    DATABASE_URL: str
    REDIS_URL: str
    
    # JWT
    SECRET_KEY: str = "default_secret_key_for_dev_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24H

    #OTP
    OTP_EXPIRE_SECONDS: int = 120 # 2m
    OTP_LENGTH: int = 6

    # read .env variables
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# build an unique instance
settings = Settings()