""" API Gateway configurations from env """

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API Gateway settings."""

    # General
    ENVIRONMENT: str 
    LOG_LEVEL: str = "INFO"
    API_GATEWAY_PORT: int = 8000
    CORRELATION_ID_HEADER: str = "X-Correlation-ID"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str 
    JWT_EXPIRY_MINUTES: int = 30

    # Cognito
    COGNITO_REGION: str
    COGNITO_USER_POOL_ID: str
    COGNITO_APP_CLIENT_ID: str
    COGNITO_DOMAIN: str
    COGNITO_REDIRECT_URI: str
    COGNITO_APP_CLIENT_SECRET: str

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # gRPC service endpoints
    GRPC_TIMEOUT: int
    GRPC_USE_TLS: bool
    
    TRANSACTION_GRPC_HOST: str = "transaction-service"
    TRANSACTION_GRPC_PORT: int = 50051
    RISK_ENGINE_GRPC_HOST: str = "risk-engine-service"
    RISK_ENGINE_GRPC_PORT: int = 50052
    NOTIFICATION_GRPC_HOST: str = "notification-service"
    NOTIFICATION_GRPC_PORT: int = 50055

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def JWKS_URL(self) -> str:
        return f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json" 
    
    @property
    def ISSUER(self):
        return f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}"
    
    @property
    def LOGIN_URL(self):
        return (
            f"{self.COGNITO_DOMAIN}/oauth2/authorize"
            f"?response_type=code"
            f"&client_id={self.COGNITO_APP_CLIENT_ID}"
            f"&redirect_uri={self.COGNITO_REDIRECT_URI}"
            f"&scope=openid+email"
        )

    @property
    def TRANSACTION_GRPC_ADDR(self) -> str:
        return f"{self.TRANSACTION_GRPC_HOST}:{self.TRANSACTION_GRPC_PORT}"

    @property
    def RISK_ENGINE_GRPC_ADDR(self) -> str:
        return f"{self.RISK_ENGINE_GRPC_HOST}:{self.RISK_ENGINE_GRPC_PORT}"

    @property
    def NOTIFICATION_GRPC_ADDR(self) -> str:
        return f"{self.NOTIFICATION_GRPC_HOST}:{self.NOTIFICATION_GRPC_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )


settings = Settings()
