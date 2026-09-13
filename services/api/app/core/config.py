import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "RippleGuard API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://rippleguard:local_password@localhost:5432/rippleguard"
    
    # Firebase Auth
    FIREBASE_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    # Test-only flag to allow synthetic test tokens in isolated unit tests
    AUTH_ALLOW_MOCK_TOKENS_FOR_TESTING: bool = False
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"
    
    # Input & Graph limits (PRD Section 7)
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_GRAPH_NODES: int = 10000
    MAX_GRAPH_EDGES: int = 50000
    
    # Enrichment
    OSV_CACHE_TTL_SECONDS: int = 21600  # 6 hours
    ENABLE_OPTIONAL_AI: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
