from functools import lru_cache

from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str
    APP_ENV: str = "local"
    APP_VERSION: str = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8088
    DEBUG: bool = 0
    SECRET_KEY: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    # OPEN AI Settings
    OPENAI_API_KEY: str

    # CORS Settings
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    # # Langchain Settings
    # LANGCHAIN_TRACING_V2: str
    # LANGCHAIN_ENDPOINT: str
    # LANGCHAIN_API_KEY: str
    # LANGCHAIN_PROJECT: str

    # # MinIO Settings
    # MINIO_ENDPOINT: str
    # MINIO_ACCESS_KEY: str
    # MINIO_SECRET_KEY: str
    # MINIO_REGION: str
    # MINIO_SECURE: bool
    # MINIO_BUCKET: str

    # # Redis
    # REDIS_HOST: str
    # REDIS_PASSWORD: str
    # REDIS_PORT: int

    # @property
    # def create_redis_url(self) -> RedisDsn:
    #     return RedisDsn.build(scheme="redis", host=self.REDIS_HOST, password=self.REDIS_PASSWORD, port=self.REDIS_PORT)

    @property
    def cors_origins(self) -> list[str]:
        return self.CORS_ALLOW_ORIGINS.split(",") if self.CORS_ALLOW_ORIGINS else []


settings = Settings()
