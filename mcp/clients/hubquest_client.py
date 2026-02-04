"""
HubQuestClient - Cliente async para API HubQuest

Implementa:
- Retry com backoff exponencial
- Paginação robusta
- Rate limiting
- Timeout configuravel
- Logging estruturado
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Erro base da API"""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class RateLimitError(APIError):
    """Erro de rate limiting"""
    pass


class TimeoutError(APIError):
    """Erro de timeout"""
    pass


@dataclass
class APIConfig:
    """Configuracao da API HubQuest"""
    base_url: str = "https://api.hubquest.com/v1"
    api_key: str = ""
    timeout: float = 30.0
    connect_timeout: float = 10.0
    max_retries: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    rate_limit_requests: int = 100
    rate_limit_window: float = 60.0  # segundos


@dataclass
class SyncResult:
    """Resultado de uma operacao de sincronizacao"""
    success: bool
    records_fetched: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    pages_processed: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    started_at: datetime = None
    completed_at: datetime = None


class HubQuestClient:
    """Cliente async para API HubQuest"""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limit_bucket: asyncio.Queue = asyncio.Queue()
        self._request_count = 0
        self._window_start = datetime.now()
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Conecta ao servidor HTTP"""
        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0
        )
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.timeout,
                write=self.config.timeout,
                pool=self.config.timeout
            ),
            limits=limits,
            http2=True  # Enable HTTP/2
        )
        
        # Initialize rate limit bucket
        for _ in range(self.config.rate_limit_requests):
            await self._rate_limit_bucket.put(1)
        
        logger.info("HubQuestClient conectado")
    
    async def disconnect(self):
        """Desconecta do servidor HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HubQuestClient desconectado")
    
    async def _acquire_rate_limit(self):
        """Adquire token do rate limiter"""
        try:
            # Try to get token with timeout
            await asyncio.wait_for(
                self._rate_limit_bucket.get(),
                timeout=self.config.rate_limit_window
            )
        except asyncio.TimeoutError:
            # Rate limit window exceeded, reset bucket
            elapsed = (datetime.now() - self._window_start).total_seconds()
            if elapsed < self.config.rate_limit_window:
                # Wait for window to reset
                await asyncio.sleep(self.config.rate_limit_window - elapsed)
            
            # Reset bucket
            while not self._rate_limit_bucket.empty():
                try:
                    self._rate_limit_bucket.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            for _ in range(self.config.rate_limit_requests):
                await self._rate_limit_bucket.put(1)
            
            self._window_start = datetime.now()
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Executa request com retry e backoff"""
        await self._acquire_rate_limit()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        
        last_error = None
        retry_delay = self.config.base_retry_delay
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", retry_delay))
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Check for timeout
                if response.status_code == 408:
                    raise TimeoutError("Request timeout", 408)
                
                # Check for other errors
                if response.status_code >= 400:
                    error_msg = response.text[:500]
                    logger.error(f"API error: {response.status_code} - {error_msg}")
                    raise APIError(
                        error_msg,
                        status_code=response.status_code,
                        response=response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    )
                
                return response.json()
                
            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Timeout: {e}", response=None)
                logger.warning(f"Timeout attempt {attempt + 1}: {e}")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    last_error = RateLimitError(f"Rate limited: {e}", 429)
                else:
                    last_error = APIError(f"HTTP error: {e}", e.response.status_code)
                logger.warning(f"HTTP error attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_error = APIError(f"Unexpected error: {e}")
                logger.warning(f"Error attempt {attempt + 1}: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries:
                await asyncio.sleep(min(retry_delay, self.config.max_retry_delay))
                retry_delay *= 2
        
        raise last_error or APIError("Max retries exceeded")
    
    async def fetch_vehicles(
        self,
        date_type: str = "atualizacao",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        state: Optional[str] = None,
        page: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Busca veiculos da API com filtros"""
        params = {
            "page": page,
            "limit": limit,
            "date_type": date_type
        }
        
        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")
        if state:
            params["state"] = state.upper()
        
        return await self._request_with_retry("GET", "/vehicles", params=params)
    
    async def fetch_vehicles_paginated(
        self,
        date_type: str = "atualizacao",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        state: Optional[str] = None,
        page_limit: int = 1000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generator async para buscar todos os veiculos paginados"""
        page = 1
        has_more = True
        
        while has_more and page <= page_limit:
            try:
                response = await self.fetch_vehicles(
                    date_type=date_type,
                    start_date=start_date,
                    end_date=end_date,
                    state=state,
                    page=page
                )
                
                results = response.get("results", [])
                pagination = response.get("pagination", {})
                
                yield {
                    "page": page,
                    "results": results,
                    "total": pagination.get("total", 0),
                    "per_page": pagination.get("per_page", 100),
                    "has_more": pagination.get("has_more", False)
                }
                
                has_more = pagination.get("has_more", False)
                page += 1
                
            except APIError as e:
                logger.error(f"Error fetching page {page}: {e}")
                has_more = False
                raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Verifica health da API"""
        return await self._request_with_retry("GET", "/health")
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Obtem status do rate limit"""
        return await self._request_with_retry("GET", "/rate-limit/status")


# Funcoes de conveniencia

async def create_client(
    api_key: str,
    base_url: str = "https://api.hubquest.com/v1"
) -> HubQuestClient:
    """Cria e conecta um novo cliente"""
    config = APIConfig(
        api_key=api_key,
        base_url=base_url
    )
    client = HubQuestClient(config)
    await client.connect()
    return client


async def test_connection(api_key: str, base_url: str = "https://api.hubquest.com/v1") -> bool:
    """Testa conexao com a API"""
    try:
        async with HubQuestClient(APIConfig(api_key=api_key, base_url=base_url)) as client:
            health = await client.check_health()
            logger.info(f"API health: {health}")
            return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
