"""Base configuration settings using Pydantic Settings."""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MicroserviceBaseSettings(BaseSettings):
    """Common microservice configuration fields."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = Field(default="microservice", description="Logical name of the microservice")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment (development, staging, production)")
    DEBUG: bool = Field(default=False, description="Debug mode")
    API_V1_PREFIX: str = Field(default="/api/v1", description="REST API prefix")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")

    # Security & JWT
    JWT_SECRET_KEY: str = Field(default="development-insecure-secret-key-change-in-production-min-32-chars", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")

    # Database
    DATABASE_URL: Optional[str] = Field(default=None, description="PostgreSQL connection string")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries in logs")

    # RabbitMQ
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/", description="RabbitMQ connection URL")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

