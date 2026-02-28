"""FastAPI MCP Server Configuration

Configuration file for the FleetIntel MCP Server.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "FleetIntel MCP Server"
    app_version: str = "0.1.0"
    app_description: str = "MCP Server for Fleet Intelligence"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    
    # Database Configuration
    database_url: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    pool_size: int = 20
    max_overflow: int = 30
    pool_recycle: int = 3600
    statement_timeout: int = 600000  # 10 minutos em milissegundos
    
    def model_post_init(self, __context):
        # Se database_url não foi definido mas SUPABASE_URL foi, usar SUPABASE_URL
        if not self.database_url and self.supabase_url:
            self.database_url = self.supabase_url
    
    # CORS Configuration
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Query Configuration
    default_limit: int = 100
    max_limit: int = 1000
    
    class Config:
        """Nested config class"""
        pass


# Settings instance
settings = Settings()
