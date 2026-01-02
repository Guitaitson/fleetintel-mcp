from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional

class BaseQueryParams(BaseModel):
    """Parâmetros base para consultas FleetIntel"""
    
    uf: str = Field(..., description="UF obrigatória (ex: SP, RJ)")
    start_date: date = Field(..., description="Data inicial (YYYY-MM-DD)")
    end_date: date = Field(..., description="Data final (YYYY-MM-DD)")
    limit: int = Field(100, le=100, description="Máximo 100 registros")
    
    @validator('uf')
    def validate_uf(cls, v):
        ufs_validas = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
        if v.upper() not in ufs_validas:
            raise ValueError(f"UF inválida. Use: {', '.join(ufs_validas)}")
        return v.upper()
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values:
            delta = v - values['start_date']
            if delta.days > 90:
                raise ValueError("Período máximo: 90 dias")
        return v

class VehicleQueryParams(BaseQueryParams):
    """Parâmetros para consulta de veículos"""
    vehicle_type: Optional[str] = Field(None, description="Tipo de veículo (ex: caminhão, van)")
    status: Optional[str] = Field(None, description="Status operacional (ativo, manutenção)")

class TripQueryParams(BaseQueryParams):
    """Parâmetros para consulta de viagens"""
    driver_id: Optional[str] = Field(None, description="ID do motorista")
    min_distance: Optional[int] = Field(None, description="Distância mínima (km)")

class DriverQueryParams(BaseQueryParams):
    """Parâmetros para consulta de motoristas"""
    license_type: Optional[str] = Field(None, description="Tipo de CNH (ex: C, D)")
    active_only: bool = Field(True, description="Apenas motoristas ativos")

class StatusQueryParams(BaseQueryParams):
    """Parâmetros para status operacional"""
    include_history: bool = Field(False, description="Incluir histórico de 24h")
    detailed: bool = Field(False, description="Detalhes completos")
