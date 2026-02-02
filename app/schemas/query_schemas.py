"""Pydantic schemas for FleetIntel MCP Server queries"""
from pydantic import BaseModel, Field
from typing import Optional, List


# Vehicle Query Schema
class VehicleQuery(BaseModel):
    """Query parameters for vehicle search"""
    chassi: Optional[str] = Field(None, description="Vehicle chassis (VIN)")
    placa: Optional[str] = Field(None, description="License plate")
    marca: Optional[str] = Field(None, description="Brand name")
    modelo: Optional[str] = Field(None, description="Model name")
    ano_fabricacao_min: Optional[int] = Field(None, description="Minimum manufacturing year")
    ano_fabricacao_max: Optional[int] = Field(None, description="Maximum manufacturing year")
    ano_modelo_min: Optional[int] = Field(None, description="Minimum model year")
    ano_modelo_max: Optional[int] = Field(None, description="Maximum model year")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")


class Vehicle(BaseModel):
    """Vehicle data model"""
    id: int
    chassi: str
    placa: str
    marca: str
    modelo: str
    ano_fabricacao: int
    ano_modelo: int


class VehicleResponse(BaseModel):
    """Vehicle query response"""
    vehicles: List[Vehicle]
    count: int


# Empresa Query Schema
class EmpresaQuery(BaseModel):
    """Query parameters for company search"""
    cnpj: Optional[str] = Field(None, description="CNPJ (exact match)")
    razao_social: Optional[str] = Field(None, description="Social security number (ILIKE)")
    nome_fantasia: Optional[str] = Field(None, description="Trade name (ILIKE)")
    segmento_cliente: Optional[str] = Field(None, description="Customer segment")
    grupo_locadora: Optional[str] = Field(None, description="Fleet company group")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")


class Empresa(BaseModel):
    """Company data model"""
    id: int
    cnpj: str
    razao_social: Optional[str]
    nome_fantasia: Optional[str]
    segmento_cliente: Optional[str]
    grupo_locadora: Optional[str]


class EmpresaResponse(BaseModel):
    """Company query response"""
    empresas: List[Empresa]
    count: int


# Registration Query Schema
class RegistrationQuery(BaseModel):
    """Query parameters for registration search"""
    data_emplacamento_inicio: Optional[str] = Field(None, description="Registration start date (ISO format)")
    data_emplacamento_fim: Optional[str] = Field(None, description="Registration end date (ISO format)")
    municipio_emplacamento: Optional[str] = Field(None, description="Registration municipality (ILIKE)")
    uf_emplacamento: Optional[str] = Field(None, description="Registration state (exact match)")
    preco_min: Optional[float] = Field(None, description="Minimum price")
    preco_max: Optional[float] = Field(None, description="Maximum price")
    preco_validado: Optional[bool] = Field(None, description="Price validated flag")
    chassi: Optional[str] = Field(None, description="Vehicle chassis")
    placa: Optional[str] = Field(None, description="License plate")
    marca: Optional[str] = Field(None, description="Brand name")
    modelo: Optional[str] = Field(None, description="Model name")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")


class Registration(BaseModel):
    """Registration data model"""
    id: int
    data_emplacamento: str
    municipio_emplacamento: str
    uf_emplacamento: str
    preco: float
    preco_validado: Optional[bool]
    chassi: str
    placa: str
    marca: str
    modelo: str
    ano_fabricacao: int
    ano_modelo: int
    cnpj: str
    razao_social: Optional[str]
    nome_fantasia: Optional[str]
    segmento_cliente: Optional[str]
    grupo_locadora: Optional[str]


class RegistrationResponse(BaseModel):
    """Registration query response"""
    registrations: List[Registration]
    count: int


# Stats Response Schema
class StatsResponse(BaseModel):
    """Database statistics response"""
    marcas: int
    modelos: int
    vehicles: int
    empresas: int
    enderecos: int
    contatos: int
    registrations: int
