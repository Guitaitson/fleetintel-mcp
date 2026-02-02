from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, SecretStr
from typing import Literal
from pathlib import Path

class Settings(BaseSettings):
    """Configurações da aplicação FleetIntel MCP"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # API Externa
    fleet_api_base_url: str = Field(..., description="URL base da API de frotas")
    fleet_api_key: SecretStr = Field(..., description="API key da API de frotas")
    fleet_api_timeout: int = Field(30, ge=5, le=120)
    fleet_api_max_retries: int = Field(3, ge=1, le=10)
    
    # Supabase
    supabase_url: str = Field(..., description="URL do Supabase")
    supabase_anon_key: str = Field(..., description="Supabase anon key")
    supabase_service_role_key: SecretStr = Field(..., description="Supabase service role key")
    supabase_pool_min_size: int = Field(1, ge=1)
    supabase_pool_max_size: int = Field(10, ge=1, le=50)
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = Field(6379, ge=1, le=65535)
    redis_password: SecretStr | None = None
    redis_db: int = Field(0, ge=0, le=15)
    redis_max_connections: int = Field(10, ge=1, le=100)
    redis_default_ttl: int = Field(3600, ge=60)
    
    # FastAPI
    server_host: str = "0.0.0.0"
    server_port: int = Field(8000, ge=1000, le=65535)
    api_v1_prefix: str = "/api/v1"
    api_secret_key: SecretStr = Field(..., description="Secret key para JWT")
    cors_origins: str = "*"
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(60, ge=1)
    rate_limit_per_hour: int = Field(1000, ge=1)
    rate_limit_per_day: int = Field(10000, ge=1)
    
    # Query Guardrails
    max_records_per_query: int = Field(100, ge=1, le=1000)
    max_date_range_days: int = Field(90, ge=1, le=365)
    
    # Sync
    sync_cron_schedule: str = "0 22 * * 0"
    sync_window_days: int = Field(7, ge=1)
    sync_overlap_days: int = Field(1, ge=0)
    
    # Monitoring
    sentry_dsn: str | None = None
    log_format: Literal["json", "text"] = "text"
    log_file_path: str | None = None
    
    # Security
    allowed_hosts: str = "localhost,127.0.0.1"
    allowed_users: str = ""
    
    # Infisical (opcional)
    infisical_client_id: str | None = None
    infisical_client_secret: SecretStr | None = None
    infisical_project_id: str | None = None
    infisical_environment: str | None = None
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")]
    
    @field_validator("allowed_hosts")
    @classmethod
    def parse_allowed_hosts(cls, v: str) -> list[str]:
        return [host.strip() for host in v.split(",")]
    
    @field_validator("allowed_users")
    @classmethod
    def parse_allowed_users(cls, v: str) -> list[str]:
        if not v:
            return []
        return [user.strip() for user in v.split(",")]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "local"

# Singleton instance
_settings: Settings | None = None

def get_settings() -> Settings:
    """Get settings instance (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Para facilitar importação
settings = get_settings()
