"""FastAPI MCP Server - FleetIntel

Main entry point for the MCP server implementation.
Includes guardrails for rate limiting, input validation, and query timeouts.
"""
from contextlib import asynccontextmanager
from typing import Optional, Any, Dict, List
import os
import sys
import asyncio
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session
import uvicorn

# Import configuration
from src.config.settings import settings

# Import database connection
from src.fleet_intel_mcp.db.connection import get_db_engine

# Import guardrails
from app.core.guardrails import (
    rate_limiter,
    InputSanitizer,
    validate_date_range,
    get_rate_limit_headers,
    GuardrailedVehicleQuery,
    GuardrailedRegistrationQuery,
    GuardrailedEmpresaQuery,
    QUERY_TIMEOUT_SECONDS,
    MAX_DATE_RANGE_DAYS
)

# Import schemas
from app.schemas.query_schemas import (
    VehicleQuery,
    VehicleResponse,
    EmpresaQuery,
    EmpresaResponse,
    RegistrationQuery,
    RegistrationResponse,
    StatsResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="FleetIntel MCP Server",
    description="MCP Server for Fleet Intelligence",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database engine with timeout settings
engine = get_db_engine()


# Dependency for database session
@asynccontextmanager
async def get_db():
    async with AsyncSession(engine) as session:
        yield session


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fleetintel-mcp-server",
        "version": "0.2.0",
        "guardrails": {
            "rate_limiting": True,
            "input_sanitization": True,
            "uf_validation": True,
            "date_range_limit_days": MAX_DATE_RANGE_DAYS,
            "query_timeout_seconds": QUERY_TIMEOUT_SECONDS
        }
    }


# Stats endpoint
@app.get("/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    """Get database statistics"""
    async with engine.begin() as conn:
        # Get counts from all tables
        tables = ['marcas', 'modelos', 'vehicles', 'empresas', 'enderecos', 'contatos', 'registrations']
        counts = {}
        
        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts[table] = result.scalar()
        
        return StatsResponse(
            marcas=counts.get('marcas', 0),
            modelos=counts.get('modelos', 0),
            vehicles=counts.get('vehicles', 0),
            empresas=counts.get('empresas', 0),
            enderecos=counts.get('enderecos', 0),
            contatos=counts.get('contatos', 0),
            registrations=counts.get('registrations', 0)
        )


# Vehicle query endpoints
@app.post("/vehicles/query", response_model=VehicleResponse, tags=["Vehicles"])
async def query_vehicles(query: GuardrailedVehicleQuery, request: Request):
    """Query vehicles by various criteria with guardrails"""
    
    # Verificar rate limit
    allowed, message = rate_limiter.check_rate_limit(request)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    start_time = time.time()
    
    try:
        async with engine.begin() as conn:
            # Build query dynamically based on provided filters
            conditions = []
            params = {}
            
            if query.chassi:
                conditions.append("chassi = :chassi")
                params['chassi'] = f"%{query.chassi}%"
            
            if query.placa:
                conditions.append("placa = :placa")
                params['placa'] = f"%{query.placa}%"
            
            if query.marca:
                conditions.append("marca_nome = :marca")
                params['marca'] = f"%{query.marca}%"
            
            if query.modelo:
                conditions.append("modelo_nome = :modelo")
                params['modelo'] = f"%{query.modelo}%"
            
            if query.ano_fabricacao_min:
                conditions.append("ano_fabricacao >= :ano_min")
                params['ano_min'] = query.ano_fabricacao_min
            
            if query.ano_fabricacao_max:
                conditions.append("ano_fabricacao <= :ano_max")
                params['ano_max'] = query.ano_fabricacao_max
            
            # Build WHERE clause
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Build query
            sql = f"""
                SELECT id, chassi, placa, marca_nome, modelo_nome, 
                       ano_fabricacao, ano_modelo
                FROM vehicles
                WHERE {where_clause}
                LIMIT :limit
            """
            
            params['limit'] = query.limit or 100
            
            # Execute query
            result = await conn.execute(text(sql), params)
            rows = result.fetchall()
            
            vehicles = [
                {
                    "id": row[0],
                    "chassi": row[1],
                    "placa": row[2],
                    "marca": row[3],
                    "modelo": row[4],
                    "ano_fabricacao": row[5],
                    "ano_modelo": row[6]
                }
                for row in rows
            ]
            
            elapsed = time.time() - start_time
            
            # Adicionar headers de rate limit
            response_headers = get_rate_limit_headers(request)
            
            return VehicleResponse(
                vehicles=vehicles,
                count=len(vehicles)
            )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Query timeout excedido ({QUERY_TIMEOUT_SECONDS}s)"
        )


# Empresa query endpoints
@app.post("/empresas/query", response_model=EmpresaResponse, tags=["Empresas"])
async def query_empresas(query: GuardrailedEmpresaQuery, request: Request):
    """Query empresas by various criteria with guardrails"""
    
    # Verificar rate limit
    allowed, message = rate_limiter.check_rate_limit(request)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    start_time = time.time()
    
    try:
        async with engine.begin() as conn:
            # Build query dynamically based on provided filters
            conditions = []
            params = {}
            
            if query.cnpj:
                conditions.append("cnpj = :cnpj")
                params['cnpj'] = query.cnpj
            
            if query.razao_social:
                conditions.append("razao_social ILIKE :razao_social")
                params['razao_social'] = f"%{query.razao_social}%"
            
            if query.nome_fantasia:
                conditions.append("nome_fantasia ILIKE :nome_fantasia")
                params['nome_fantasia'] = f"%{query.nome_fantasia}%"
            
            if query.segmento_cliente:
                conditions.append("segmento_cliente = :segmento")
                params['segmento'] = query.segmento_cliente
            
            if query.grupo_locadora:
                conditions.append("grupo_locadora = :grupo")
                params['grupo'] = query.grupo_locadora
            
            # Build WHERE clause
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Build query
            sql = f"""
                SELECT id, cnpj, razao_social, nome_fantasia, 
                       segmento_cliente, grupo_locadora
                FROM empresas
                WHERE {where_clause}
                LIMIT :limit
            """
            
            params['limit'] = query.limit or 100
            
            # Execute query
            result = await conn.execute(text(sql), params)
            rows = result.fetchall()
            
            empresas = [
                {
                    "id": row[0],
                    "cnpj": row[1],
                    "razao_social": row[2],
                    "nome_fantasia": row[3],
                    "segmento_cliente": row[4],
                    "grupo_locadora": row[5]
                }
                for row in rows
            ]
            
            return EmpresaResponse(
                empresas=empresas,
                count=len(empresas)
            )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Query timeout excedido ({QUERY_TIMEOUT_SECONDS}s)"
        )


# Registration query endpoints
@app.post("/registrations/query", response_model=RegistrationResponse, tags=["Registrations"])
async def query_registrations(query: GuardrailedRegistrationQuery, request: Request):
    """Query registrations by various criteria with guardrails
    
    ATENCAO: UF e obrigatoria para todas as consultas de registrations!
    """
    
    # Verificar rate limit
    allowed, message = rate_limiter.check_rate_limit(request)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    # Validar periodo de datas
    if query.data_emplacamento_inicio or query.data_emplacamento_fim:
        start_date, end_date = validate_date_range(
            query.data_emplacamento_inicio,
            query.data_emplacamento_fim,
            "data_emplacamento_inicio",
            "data_emplacamento_fim"
        )
        # Atualizar datas validadas
        query.data_emplacamento_inicio = start_date.strftime("%Y-%m-%d")
        query.data_emplacamento_fim = end_date.strftime("%Y-%m-%d")
    
    start_time = time.time()
    
    try:
        async with engine.begin() as conn:
            # Build query dynamically based on provided filters
            conditions = ["uf_emplacamento = :uf"]  # UF obrigatoria!
            params = {'uf': query.uf_emplacamento}
            
            if query.data_emplacamento_inicio:
                conditions.append("data_emplacamento >= :data_inicio")
                params['data_inicio'] = query.data_emplacamento_inicio
            
            if query.data_emplacamento_fim:
                conditions.append("data_emplacamento <= :data_fim")
                params['data_fim'] = query.data_emplacamento_fim
            
            if query.municipio_emplacamento:
                conditions.append("municipio_emplacamento ILIKE :municipio")
                params['municipio'] = f"%{query.municipio_emplacamento}%"
            
            if query.chassi:
                conditions.append("v.chassi = :chassi")
                params['chassi'] = f"%{query.chassi}%"
            
            if query.placa:
                conditions.append("v.placa = :placa")
                params['placa'] = f"%{query.placa}%"
            
            if query.marca:
                conditions.append("v.marca_nome = :marca")
                params['marca'] = f"%{query.marca}%"
            
            if query.modelo:
                conditions.append("v.modelo_nome = :modelo")
                params['modelo'] = f"%{query.modelo}%"
            
            # Build WHERE clause
            where_clause = " AND ".join(conditions)
            
            # Build query
            sql = f"""
                SELECT r.id, r.data_emplacamento, r.municipio_emplacamento, r.uf_emplacamento,
                       r.preco, r.preco_validado,
                       v.chassi, v.placa, v.ano_fabricacao, v.ano_modelo,
                       e.cnpj, e.razao_social
                FROM registrations r
                JOIN vehicles v ON r.vehicle_id = v.id
                JOIN empresas e ON r.empresa_id = e.id
                WHERE {where_clause}
                LIMIT :limit
            """
            
            params['limit'] = query.limit or 100
            
            # Execute query
            result = await conn.execute(text(sql), params)
            rows = result.fetchall()
            
            registrations = [
                {
                    "id": row[0],
                    "data_emplacamento": str(row[1]),
                    "municipio_emplacamento": row[2],
                    "uf_emplacamento": row[3],
                    "preco": float(row[4]) if row[4] else None,
                    "preco_validado": row[5],
                    "chassi": row[6],
                    "placa": row[7],
                    "ano_fabricacao": row[8],
                    "ano_modelo": row[9],
                    "cnpj": row[10],
                    "razao_social": row[11]
                }
                for row in rows
            ]
            
            return RegistrationResponse(
                registrations=registrations,
                count=len(registrations)
            )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Query timeout excedido ({QUERY_TIMEOUT_SECONDS}s)"
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "FleetIntel MCP Server",
        "version": "0.1.0",
        "description": "MCP Server for Fleet Intelligence",
        "endpoints": {
            "health": "GET /health - Health check",
            "stats": "GET /stats - Database statistics",
            "vehicles": "POST /vehicles/query - Query vehicles",
            "empresas": "POST /empresas/query - Query empresas",
            "registrations": "POST /registrations/query - Query registrations",
        },
        "documentation": "/docs - API documentation"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url.path)
    }


# Run server
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("FleetIntel MCP Server v0.2.0")
    print("=" * 60)
    print(f"Rate Limit: 20 consultas/hora, 200/dia")
    print(f"Date Range Max: {MAX_DATE_RANGE_DAYS} dias")
    print(f"Query Timeout: {QUERY_TIMEOUT_SECONDS} segundos")
    print(f"Starting server on http://0.0.0.0:8000")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
