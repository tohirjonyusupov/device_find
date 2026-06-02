from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""  # .env da ko'rsatilishi shart
    SECRET_KEY: str = "device-guard-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    FRONTEND_URL: str = "http://localhost:5500"

    class Config:
        env_file = ".env"


settings = Settings()
