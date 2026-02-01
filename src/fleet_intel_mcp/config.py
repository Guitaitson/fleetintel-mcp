from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: str
    admin_api_key: str = Field(default="", env="ADMIN_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
