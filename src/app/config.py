from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PagePulse"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-random-secret-key"

    database_url: str = "sqlite+aiosqlite:///./pagepulse.db"

    jwt_secret_key: str = "change-me-to-a-random-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
