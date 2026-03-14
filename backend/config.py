from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    GROQ_API_KEY: str = ""  # for AI filter extraction via Groq
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
