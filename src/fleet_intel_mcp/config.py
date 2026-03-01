from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/1"
    mcp_auth_token: str = Field(default="", description="Bearer token para autenticacao do MCP HTTP server")
    admin_api_key: str = Field(default="")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
