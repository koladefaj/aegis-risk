"""Risk Engine Service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Risk Engine settings."""

    ENVIRONMENT: str
    LOG_LEVEL: str = "INFO"

    # gRPC
    RISK_ENGINE_GRPC_PORT: int = 50052

    # Database
    POSTGRES_USER: str 
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str 
    POSTGRES_PORT: int 
    RISK_DB_NAME: str 

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
    SQS_RISK_COMPLETED_QUEUE: str
    SQS_TRANSACTION_DLQ: str

    # Worker config
    WORKER_POLL_INTERVAL: int = 5
    WORKER_VISIBILITY_TIMEOUT: int = 30
    WORKER_MAX_MESSAGES: int = 10
    WORKER_ID: str = "risk-worker-1"

    # gRPC downstream services
    ML_SERVICE_GRPC_HOST: str = "ml-service"
    ML_SERVICE_GRPC_PORT: int
    LLM_SERVICE_GRPC_HOST: str = "llm-service"
    LLM_SERVICE_GRPC_PORT: int
    TRANSACTION_GRPC_HOST: str = "transaction-service"
    TRANSACTION_GRPC_PORT: int

    # Risk scoring weights
    RULE_SCORE_WEIGHT: float = 0.6
    ML_SCORE_WEIGHT: float = 0.4

    # Rule thresholds (configurable)
    HIGH_VALUE_THRESHOLD: float = 10000.0
    VELOCITY_MAX_TRANSACTIONS: int = 10
    VELOCITY_WINDOW_MINUTES: int = 60
    UNUSUAL_HOUR_START: int = 0  # midnight
    UNUSUAL_HOUR_END: int = 5    # 5 AM
    ACCOUNT_AGE_RISK_DAYS: int = 30
    FAILED_BURST_THRESHOLD: int = 5
    FAILED_BURST_WINDOW_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.RISK_DB_NAME}"
        )
    
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def ML_GRPC_ADDR(self) -> str:
        return f"{self.ML_SERVICE_GRPC_HOST}:{self.ML_SERVICE_GRPC_PORT}"

    @property
    def LLM_GRPC_ADDR(self) -> str:
        return f"{self.LLM_SERVICE_GRPC_HOST}:{self.LLM_SERVICE_GRPC_PORT}"

    @property
    def TRANSACTION_GRPC_ADDR(self) -> str:
        return f"{self.TRANSACTION_GRPC_HOST}:{self.TRANSACTION_GRPC_PORT}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )


settings = Settings()
