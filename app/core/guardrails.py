"""Guardrails para FleetIntel MCP Server

Implementa validacoes de seguranca e limitacao de consultas.
"""
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel, Field, validator
from collections import defaultdict
import hashlib


# ============================================================
# CONFIGURACOES DE GUARDRAILS
# ============================================================

RATE_LIMIT_HOURLY = 20       # Maximo consultas por hora
RATE_LIMIT_DAILY = 200       # Maximo consultas por dia
QUERY_TIMEOUT_SECONDS = 30   # Timeout de query
MAX_DATE_RANGE_DAYS = 90     # Maximo periodo por consulta
MAX_RESULTS_LIMIT = 1000     # Maximo registros por consulta


# ============================================================
# RATE LIMITING (IN-MEMORY)
# ============================================================

class RateLimiter:
    """Rate limiter em memoria para consultas"""
    
    def __init__(self):
        self._hourly: Dict[str, list] = defaultdict(list)
        self._daily: Dict[str, list] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Identifica cliente por IP ou API key"""
        # Tentar obter API key do header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key[:8]}"
        
        # Fallback para IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _cleanup_old_entries(self, timestamps: list, max_age_seconds: int) -> list:
        """Remove entradas mais antigas que o limite"""
        cutoff = time.time() - max_age_seconds
        return [t for t in timestamps if t > cutoff]
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, str]:
        """Verifica limite de consultas
        
        Returns:
            (is_allowed, message)
        """
        client_id = self._get_client_id(request)
        now = time.time()
        
        # Cleanup
        self._hourly[client_id] = self._cleanup_old_entries(
            self._hourly[client_id], 3600
        )
        self._daily[client_id] = self._cleanup_old_entries(
            self._daily[client_id], 86400
        )
        
        # Verificar limite horario
        hourly_count = len(self._hourly[client_id])
        if hourly_count >= RATE_LIMIT_HOURLY:
            return False, f"Limite horario excedido ({RATE_LIMIT_HOURLY}/hora)"
        
        # Verificar limite diario
        daily_count = len(self._daily[client_id])
        if daily_count >= RATE_LIMIT_DAILY:
            return False, f"Limite diario excedido ({RATE_LIMIT_DAILY}/dia)"
        
        # Registrar consulta
        self._hourly[client_id].append(now)
        self._daily[client_id].append(now)
        
        return True, "OK"
    
    def get_remaining(self, request: Request) -> Dict[str, int]:
        """Retorna consultas restantes"""
        client_id = self._get_client_id(request)
        now = time.time()
        
        hourly_remaining = max(0, RATE_LIMIT_HOURLY - len(
            self._cleanup_old_entries(self._hourly[client_id], 3600)
        ))
        daily_remaining = max(0, RATE_LIMIT_DAILY - len(
            self._cleanup_old_entries(self._daily[client_id], 86400)
        ))
        
        return {
            "hourly_remaining": hourly_remaining,
            "daily_remaining": daily_remaining
        }


# Instancia global do rate limiter
rate_limiter = RateLimiter()


# ============================================================
# INPUT SANITIZATION
# ============================================================

class InputSanitizer:
    """Sanitizacao de inputs para prevencao de injection"""
    
    # Padrões perigosos
    DANGEROUS_PATTERNS = [
        r"['\";].*(DROP|DELETE|TRUNCATE|INSERT|UPDATE|ALTER)",  # SQL injection
        r"\$\$",                                                 # PostgreSQL dollar quotes
        r"--",                                                   # SQL comments
        r"\/\*.*\*\/",                                           # SQL block comments
        r";.*;(DROP|DELETE|TRUNCATE|INSERT|UPDATE|ALTER)",      # Multiple statements
        r"\x00",                                                 # Null bytes
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, field_name: str) -> str:
        """Sanitiza string, removendo caracteres perigosos"""
        if not value:
            return value
        
        # Verificar padrões perigosos
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail=f"Input invalido em '{field_name}': caracteres perigosos detectados"
                )
        
        # Remover caracteres de controle
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
        
        # Limitar tamanho
        max_length = 255
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @classmethod
    def sanitize_cnpj(cls, cnpj: str) -> str:
        """Sanitiza CNPJ"""
        if not cnpj:
            return cnpj
        # Remover caracteres nao numericos
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        # Validar tamanho
        if len(cnpj) != 14:
            raise HTTPException(
                status_code=400,
                detail="CNPJ deve ter 14 digitos"
            )
        return cnpj
    
    @classmethod
    def sanitize_cep(cls, cep: str) -> str:
        """Sanitiza CEP"""
        if not cep:
            return cep
        # Remover caracteres nao numericos
        cep = re.sub(r'[^0-9]', '', cep)
        # Validar tamanho
        if len(cep) != 8:
            raise HTTPException(
                status_code=400,
                detail="CEP deve ter 8 digitos"
            )
        return cep
    
    @classmethod
    def sanitize_uf(cls, uf: str) -> str:
        """Sanitiza UF (estado brasileiro)"""
        if not uf:
            return uf
        # Converter para maiusculas e remover caracteres invalidos
        uf = re.sub(r'[^A-Z]', '', uf.upper())
        # Validar UF
        valid_ufs = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        if uf not in valid_ufs:
            raise HTTPException(
                status_code=400,
                detail=f"UF invalida: {uf}. UFs validas: {', '.join(valid_ufs)}"
            )
        return uf


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    field_name_start: str = "start_date",
    field_name_end: str = "end_date"
) -> Tuple[datetime, datetime]:
    """Valida periodo de datas (maximo 90 dias)
    
    Returns:
        (start_date, end_date) como datetime
    
    Raises:
        HTTPException: Se periodo invalido
    """
    # Converter datas
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Data inicial invalida: {start_date}. Formato esperado: YYYY-MM-DD"
        )
    
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Data final invalida: {end_date}. Formato esperado: YYYY-MM-DD"
        )
    
    # Validar logica
    if start and end:
        if start > end:
            raise HTTPException(
                status_code=400,
                detail="Data inicial deve ser anterior a data final"
            )
        
        diff = (end - start).days
        if diff > MAX_DATE_RANGE_DAYS:
            raise HTTPException(
                status_code=400,
                detail=f"Periodo maximo excedido: {diff} dias. Limite: {MAX_DATE_RANGE_DAYS} dias"
            )
    
    # Se nao fornecida data final, usar hoje
    if start and not end:
        end = datetime.now()
        diff = (end - start).days
        if diff > MAX_DATE_RANGE_DAYS:
            raise HTTPException(
                status_code=400,
                detail=f"Periodo maximo excedido: {diff} dias. Limite: {MAX_DATE_RANGE_DAYS} dias"
            )
    
    # Se nao fornecida data inicial, usar 90 dias atras
    if not start and end:
        start = end - timedelta(days=MAX_DATE_RANGE_DAYS)
    
    return start, end


# ============================================================
# QUERY SCHEMAS COM GUARDRAILS
# ============================================================

class GuardrailedVehicleQuery(BaseModel):
    """Vehicle query com guardrails"""
    chassi: Optional[str] = Field(None, max_length=17)
    placa: Optional[str] = Field(None, max_length=7)
    marca: Optional[str] = Field(None, max_length=50)
    modelo: Optional[str] = Field(None, max_length=50)
    ano_fabricacao_min: Optional[int] = Field(None, ge=1980, le=2030)
    ano_fabricacao_max: Optional[int] = Field(None, ge=1980, le=2030)
    ano_modelo_min: Optional[int] = Field(None, ge=1980, le=2030)
    ano_modelo_max: Optional[int] = Field(None, ge=1980, le=2030)
    limit: int = Field(100, ge=1, le=MAX_RESULTS_LIMIT)
    
    @validator('chassi', 'placa', pre=True, always=True)
    def sanitize_chassi_placa(cls, v):
        if v:
            return InputSanitizer.sanitize_string(v, 'chassi/placa')
        return v
    
    @validator('marca', 'modelo', pre=True, always=True)
    def sanitize_text_fields(cls, v, field):
        if v:
            return InputSanitizer.sanitize_string(v, field.name)
        return v


class GuardrailedRegistrationQuery(BaseModel):
    """Registration query com guardrails obrigatorios"""
    data_emplacamento_inicio: Optional[str] = Field(None, description="Data inicial (YYYY-MM-DD)")
    data_emplacamento_fim: Optional[str] = Field(None, description="Data final (YYYY-MM-DD)")
    uf_emplacamento: str = Field(..., description="UF obrigatoria")
    municipio_emplacamento: Optional[str] = Field(None, max_length=100)
    chassi: Optional[str] = Field(None, max_length=17)
    placa: Optional[str] = Field(None, max_length=7)
    marca: Optional[str] = Field(None, max_length=50)
    modelo: Optional[str] = Field(None, max_length=50)
    limit: int = Field(100, ge=1, le=MAX_RESULTS_LIMIT)
    
    @validator('uf_emplacamento', pre=True, always=True)
    def validate_uf(cls, v):
        if not v:
            raise HTTPException(
                status_code=400,
                detail="UF e obrigatoria para consultas de registrations"
            )
        return InputSanitizer.sanitize_uf(v)
    
    @validator('municipio_emplacamento', 'chassi', 'placa', 'marca', 'modelo', pre=True, always=True)
    def sanitize_fields(cls, v, field):
        if v:
            return InputSanitizer.sanitize_string(v, field.name)
        return v
    
    @validator('data_emplacamento_inicio', 'data_emplacamento_fim', pre=True, always=True)
    def validate_dates(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Data invalida: {v}. Formato: YYYY-MM-DD"
                )
        return v


class GuardrailedEmpresaQuery(BaseModel):
    """Empresa query com guardrails"""
    cnpj: Optional[str] = Field(None, min_length=14, max_length=14)
    razao_social: Optional[str] = Field(None, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    segmento_cliente: Optional[str] = Field(None, max_length=50)
    grupo_locadora: Optional[str] = Field(None, max_length=50)
    limit: int = Field(100, ge=1, le=MAX_RESULTS_LIMIT)
    
    @validator('cnpj', pre=True, always=True)
    def validate_cnpj(cls, v):
        if v:
            return InputSanitizer.sanitize_cnpj(v)
        return v
    
    @validator('razao_social', 'nome_fantasia', 'segmento_cliente', 'grupo_locadora', pre=True, always=True)
    def sanitize_text_fields(cls, v, field):
        if v:
            return InputSanitizer.sanitize_string(v, field.name)
        return v


# ============================================================
# DEPENDENCY FOR RATE LIMITING
# ============================================================

async def check_rate_limit(request: Request):
    """Dependency para verificar rate limit"""
    allowed, message = rate_limiter.check_rate_limit(request)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_rate_limit_headers(request: Request) -> Dict[str, str]:
    """Retorna headers de rate limit"""
    remaining = rate_limiter.get_remaining(request)
    return {
        "X-RateLimit-Hourly-Limit": str(RATE_LIMIT_HOURLY),
        "X-RateLimit-Hourly-Remaining": str(remaining["hourly_remaining"]),
        "X-RateLimit-Daily-Limit": str(RATE_LIMIT_DAILY),
        "X-RateLimit-Daily-Remaining": str(remaining["daily_remaining"]),
        "X-RateLimit-Max-Days": str(MAX_DATE_RANGE_DAYS),
        "X-Query-Timeout-Secs": str(QUERY_TIMEOUT_SECONDS),
    }
