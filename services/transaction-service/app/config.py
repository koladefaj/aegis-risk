""" Transaction Seervice configuration. """

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Transaction service settings."""

    ENVIRONMENT: str 
    LOG_LEVEL: str = "INFO"

    # gRPC
    TRANSACTION_GRPC_PORT: int

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str 
    POSTGRES_HOST: str 
    POSTGRES_PORT: int 
    TRANSACTION_DB_NAME: str

    # Redis (for idempotency cache)
    REDIS_HOST: str 
    REDIS_PORT: int
    REDIS_DB: int

    # SQS
    AWS_REGION: str 
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str 
    AWS_ENDPOINT_URL: str 
    SQS_TRANSACTION_QUEUE: str

    #DATABASE_URL = "postgresql+asyncpg://aegis:aegis_secret@localhost:5432/<service_db_name>"
    #docker compose run --rm <service-name> alembic upgrade head

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.TRANSACTION_DB_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.TRANSACTION_DB_NAME}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )


settings = Settings()
