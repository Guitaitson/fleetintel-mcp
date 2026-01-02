from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # User Management
    MAX_USERS_MVP: int = 5
    MAX_DEVICES_PER_USER: int = 3
    
    # Query Limits
    MAX_RECORDS_PER_QUERY: int = 100
    MAX_QUERIES_PER_HOUR: int = 20
    MAX_QUERIES_PER_DAY: int = 200
    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_DATE_RANGE_DAYS: int = 90
    
    # Cache Settings
    CACHE_TTL_VEHICLE: int = 86400  # 24h
    CACHE_TTL_STATUS: int = 300      # 5min
    CACHE_TTL_LOCATION: int = 60     # 1min
    CACHE_TTL_TRIPS: int = 3600      # 1h
    CACHE_TTL_REPORTS: int = 21600   # 6h
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    REQUIRE_UF_FILTER: bool = True
    LOG_ALL_QUERIES: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def validate_settings(settings: Settings):
    # Implementar validações complexas se necessário
    pass
