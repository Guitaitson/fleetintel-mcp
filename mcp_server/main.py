"""FleetIntel MCP Server — Plataforma de dados de frotas via MCP HTTP

Servidor MCP que expoe tools para consultar veiculos, empresas e registros
de emplacamento. Acessivel por qualquer agente via HTTP (Streamable HTTP
transport) com autenticacao Bearer token.

Uso:
    python -m mcp_server.main

Variaveis de ambiente:
    DATABASE_URL     PostgreSQL connection string (asyncpg)
    MCP_AUTH_TOKEN   Bearer token para autenticacao (vazio = sem auth)
    MCP_PORT         Porta HTTP (padrao: 8888)
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy import text

from src.fleet_intel_mcp.db.connection import AsyncSessionLocal
from src.fleet_intel_mcp.config import settings

# =============================================================================
# INICIALIZACAO DO SERVIDOR
# =============================================================================

MCP_PORT = int(os.getenv("MCP_PORT", "8888"))

mcp = FastMCP(
    name="fleetintel-mcp",
    instructions=(
        "Servidor de inteligencia de frotas. "
        "Consulte veiculos, empresas proprietarias e registros de emplacamento "
        "no mercado brasileiro. Use as tools para buscar, filtrar e agregar dados."
    ),
    host="0.0.0.0",
    port=MCP_PORT,
)


# =============================================================================
# HELPERS: FORMATADORES
# =============================================================================

def _fmt_vehicle(row: Any) -> dict:
    return {
        "id": row.get("id"),
        "chassi": row.get("chassi"),
        "placa": row.get("placa"),
        "marca": row.get("marca_nome"),
        "modelo": row.get("modelo_nome"),
        "ano_fabricacao": row.get("ano_fabricacao"),
        "ano_modelo": row.get("ano_modelo"),
    }


def _fmt_empresa(row: Any) -> dict:
    return {
        "id": row.get("id"),
        "cnpj": row.get("cnpj"),
        "razao_social": row.get("razao_social"),
        "nome_fantasia": row.get("nome_fantasia"),
        "segmento_cliente": row.get("segmento_cliente"),
        "grupo_locadora": row.get("grupo_locadora"),
    }


def _fmt_registration(row: Any) -> dict:
    return {
        "id": row.get("id"),
        "data_emplacamento": str(row.get("data_emplacamento")),
        "municipio_emplacamento": row.get("municipio_emplacamento"),
        "uf_emplacamento": row.get("uf_emplacamento"),
        "preco": row.get("preco"),
        "preco_validado": row.get("preco_validado"),
        "chassi": row.get("chassi"),
        "placa": row.get("placa"),
        "marca": row.get("marca_nome"),
        "modelo": row.get("modelo_nome"),
        "ano_fabricacao": row.get("ano_fabricacao"),
        "ano_modelo": row.get("ano_modelo"),
        "cnpj": row.get("cnpj"),
        "razao_social": row.get("razao_social"),
        "nome_fantasia": row.get("nome_fantasia"),
        "segmento_cliente": row.get("segmento_cliente"),
        "grupo_locadora": row.get("grupo_locadora"),
    }


# =============================================================================
# TOOLS
# =============================================================================

@mcp.tool()
async def search_vehicles(
    chassi: Optional[str] = None,
    placa: Optional[str] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    ano_fabricacao_min: Optional[int] = None,
    ano_fabricacao_max: Optional[int] = None,
    limit: int = 100,
) -> dict:
    """Busca veiculos por chassi, placa, marca, modelo ou faixa de ano.

    Retorna dados de cada veiculo: id, chassi, placa, marca, modelo e ano.
    Use limit para controlar o numero de resultados (maximo 1000).
    """
    conditions = []
    params: dict = {}

    if chassi:
        conditions.append("chassi = :chassi")
        params["chassi"] = chassi
    if placa:
        conditions.append("placa ILIKE :placa")
        params["placa"] = f"{placa}%"
    if marca:
        conditions.append("marca_nome ILIKE :marca")
        params["marca"] = f"{marca}%"
    if modelo:
        conditions.append("modelo_nome ILIKE :modelo")
        params["modelo"] = f"{modelo}%"
    if ano_fabricacao_min:
        conditions.append("ano_fabricacao >= :ano_min")
        params["ano_min"] = ano_fabricacao_min
    if ano_fabricacao_max:
        conditions.append("ano_fabricacao <= :ano_max")
        params["ano_max"] = ano_fabricacao_max

    where = " AND ".join(conditions) if conditions else "1=1"
    params["limit"] = min(limit, 1000)

    query = text(f"""
        SELECT id, chassi, placa, marca_nome, modelo_nome, ano_fabricacao, ano_modelo
        FROM vehicles
        WHERE {where}
        ORDER BY id
        LIMIT :limit
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, params)
        rows = result.fetchall()

    vehicles = [_fmt_vehicle(row._mapping) for row in rows]
    return {"vehicles": vehicles, "count": len(vehicles), "timestamp": datetime.utcnow().isoformat()}


@mcp.tool()
async def search_empresas(
    cnpj: Optional[str] = None,
    razao_social: Optional[str] = None,
    nome_fantasia: Optional[str] = None,
    segmento_cliente: Optional[str] = None,
    grupo_locadora: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """Busca empresas proprietarias de frota por CNPJ, razao social, nome fantasia ou segmento.

    Retorna id, CNPJ, razao social, nome fantasia, segmento e grupo locadora.
    """
    conditions = []
    params: dict = {}

    if cnpj:
        conditions.append("cnpj = :cnpj")
        params["cnpj"] = cnpj
    if razao_social:
        conditions.append("razao_social ILIKE :razao_social")
        params["razao_social"] = f"%{razao_social}%"
    if nome_fantasia:
        conditions.append("nome_fantasia ILIKE :nome_fantasia")
        params["nome_fantasia"] = f"%{nome_fantasia}%"
    if segmento_cliente:
        conditions.append("segmento_cliente ILIKE :segmento")
        params["segmento"] = f"%{segmento_cliente}%"
    if grupo_locadora:
        conditions.append("grupo_locadora ILIKE :grupo")
        params["grupo"] = f"%{grupo_locadora}%"

    where = " AND ".join(conditions) if conditions else "1=1"
    params["limit"] = min(limit, 1000)

    query = text(f"""
        SELECT id, cnpj, razao_social, nome_fantasia, segmento_cliente, grupo_locadora
        FROM empresas
        WHERE {where}
        ORDER BY id
        LIMIT :limit
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, params)
        rows = result.fetchall()

    empresas = [_fmt_empresa(row._mapping) for row in rows]
    return {"empresas": empresas, "count": len(empresas), "timestamp": datetime.utcnow().isoformat()}


@mcp.tool()
async def search_registrations(
    data_emplacamento_inicio: Optional[str] = None,
    data_emplacamento_fim: Optional[str] = None,
    municipio_emplacamento: Optional[str] = None,
    uf_emplacamento: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    preco_validado: Optional[bool] = None,
    chassi: Optional[str] = None,
    placa: Optional[str] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    empresa_id: Optional[int] = None,
    limit: int = 100,
) -> dict:
    """Busca registros de emplacamento por periodo, UF, municipio, preco ou veiculo/empresa.

    Retorna dados completos: data, local, preco, veiculo e empresa proprietaria.
    """
    conditions = []
    params: dict = {}

    if data_emplacamento_inicio:
        conditions.append("r.data_emplacamento >= :data_inicio")
        params["data_inicio"] = data_emplacamento_inicio
    if data_emplacamento_fim:
        conditions.append("r.data_emplacamento <= :data_fim")
        params["data_fim"] = data_emplacamento_fim
    if municipio_emplacamento:
        conditions.append("r.municipio_emplacamento ILIKE :municipio")
        params["municipio"] = f"%{municipio_emplacamento}%"
    if uf_emplacamento:
        conditions.append("r.uf_emplacamento = :uf")
        params["uf"] = uf_emplacamento
    if preco_min is not None:
        conditions.append("r.preco >= :preco_min")
        params["preco_min"] = preco_min
    if preco_max is not None:
        conditions.append("r.preco <= :preco_max")
        params["preco_max"] = preco_max
    if preco_validado is not None:
        conditions.append("r.preco_validado = :preco_validado")
        params["preco_validado"] = preco_validado
    if chassi:
        conditions.append("v.chassi = :chassi")
        params["chassi"] = chassi
    if placa:
        conditions.append("v.placa ILIKE :placa")
        params["placa"] = f"{placa}%"
    if marca:
        conditions.append("v.marca_nome ILIKE :marca")
        params["marca"] = f"{marca}%"
    if modelo:
        conditions.append("v.modelo_nome ILIKE :modelo")
        params["modelo"] = f"{modelo}%"
    if empresa_id:
        conditions.append("r.empresa_id = :empresa_id")
        params["empresa_id"] = empresa_id

    where = " AND ".join(conditions) if conditions else "1=1"
    params["limit"] = min(limit, 1000)

    query = text(f"""
        SELECT r.id, r.data_emplacamento, r.municipio_emplacamento, r.uf_emplacamento,
               r.preco, r.preco_validado,
               v.chassi, v.placa, v.marca_nome, v.modelo_nome, v.ano_fabricacao, v.ano_modelo,
               e.cnpj, e.razao_social, e.nome_fantasia, e.segmento_cliente, e.grupo_locadora
        FROM registrations r
        JOIN vehicles v ON r.vehicle_id = v.id
        JOIN empresas e ON r.empresa_id = e.id
        WHERE {where}
        ORDER BY r.data_emplacamento DESC
        LIMIT :limit
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, params)
        rows = result.fetchall()

    regs = [_fmt_registration(row._mapping) for row in rows]
    return {"registrations": regs, "count": len(regs), "timestamp": datetime.utcnow().isoformat()}


@mcp.tool()
async def get_stats() -> dict:
    """Retorna contagens de todos os dados no banco: marcas, modelos, veiculos, empresas e emplacamentos."""
    tables = ["marcas", "modelos", "vehicles", "empresas", "enderecos", "contatos", "registrations"]
    stats: dict = {}

    async with AsyncSessionLocal() as session:
        for table in tables:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            stats[table] = result.scalar() or 0

    return {"stats": stats, "timestamp": datetime.utcnow().isoformat()}


@mcp.tool()
async def top_empresas_by_registrations(
    ano: int,
    uf: Optional[str] = None,
    top_n: int = 10,
) -> dict:
    """Retorna as top N empresas por numero de emplacamentos em um ano.

    Util para perguntas como: 'Quais empresas mais compraram veiculos em 2025?'
    Retorna razao social, segmento, total de emplacamentos e valor total.
    """
    conditions = ["EXTRACT(YEAR FROM r.data_emplacamento) = :ano"]
    params: dict = {"ano": ano, "top_n": top_n}

    if uf:
        conditions.append("r.uf_emplacamento = :uf")
        params["uf"] = uf

    where = " AND ".join(conditions)

    query = text(f"""
        SELECT e.id, e.razao_social, e.nome_fantasia, e.segmento_cliente,
               COUNT(r.id) as total_registrations,
               SUM(r.preco) as total_valor
        FROM empresas e
        JOIN registrations r ON e.id = r.empresa_id
        WHERE {where}
        GROUP BY e.id, e.razao_social, e.nome_fantasia, e.segmento_cliente
        ORDER BY total_registrations DESC
        LIMIT :top_n
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, params)
        rows = result.fetchall()

    empresas = [
        {
            "id": row.id,
            "razao_social": row.razao_social,
            "nome_fantasia": row.nome_fantasia,
            "segmento": row.segmento_cliente,
            "total_registrations": row.total_registrations,
            "total_valor": float(row.total_valor) if row.total_valor else 0.0,
        }
        for row in rows
    ]
    return {"empresas": empresas, "count": len(empresas), "ano": ano, "uf": uf, "timestamp": datetime.utcnow().isoformat()}


@mcp.tool()
async def count_empresa_registrations(
    razao_social: str,
    ano: Optional[int] = None,
    nome_fantasia: Optional[str] = None,
) -> dict:
    """Conta emplacamentos de uma empresa especifica por nome e ano.

    Util para perguntas como: 'Quantos caminhoes a Adiante comprou em 2025?'
    Se encontrar multiplas empresas com nomes similares, retorna lista para desambiguacao.
    """
    params: dict = {"limit": 10}
    conditions = ["(razao_social ILIKE :nome OR nome_fantasia ILIKE :nome)"]
    params["nome"] = f"%{razao_social}%"

    if nome_fantasia:
        conditions.append("nome_fantasia ILIKE :nf")
        params["nf"] = f"%{nome_fantasia}%"

    where = " AND ".join(conditions)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(f"SELECT id, cnpj, razao_social, nome_fantasia, segmento_cliente, grupo_locadora FROM empresas WHERE {where} ORDER BY id LIMIT :limit"),
            params,
        )
        empresas = result.fetchall()

    if not empresas:
        return {"count": 0, "empresas": [], "error": "Empresa nao encontrada", "suggestion": "Tente buscar por CNPJ ou parte do nome"}

    if len(empresas) > 1:
        return {
            "count": 0,
            "empresas": [dict(e._mapping) for e in empresas],
            "ambiguous": True,
            "message": f"{len(empresas)} empresas encontradas — qual voce quer dizer?",
        }

    empresa = empresas[0]
    count_params: dict = {"empresa_id": empresa.id}
    if ano:
        count_q = text("SELECT COUNT(*) FROM registrations WHERE empresa_id = :empresa_id AND EXTRACT(YEAR FROM data_emplacamento) = :ano")
        count_params["ano"] = ano
    else:
        count_q = text("SELECT COUNT(*) FROM registrations WHERE empresa_id = :empresa_id")

    async with AsyncSessionLocal() as session:
        count = (await session.execute(count_q, count_params)).scalar() or 0

    return {
        "count": count,
        "empresas": [dict(empresa._mapping)],
        "ano": ano,
        "ambiguous": False,
        "timestamp": datetime.utcnow().isoformat(),
    }


@mcp.tool()
async def get_market_share(
    ano: int,
    uf: Optional[str] = None,
    top_n: int = 10,
) -> dict:
    """Calcula o market share de marcas de veiculos por numero de emplacamentos em um ano.

    Retorna ranking de marcas com percentual de participacao de mercado.
    Optionally filtra por estado (UF).
    """
    conditions = ["EXTRACT(YEAR FROM r.data_emplacamento) = :ano"]
    params: dict = {"ano": ano}

    if uf:
        conditions.append("r.uf_emplacamento = :uf")
        params["uf"] = uf

    where = " AND ".join(conditions)

    query = text(f"""
        WITH totais AS (
            SELECT COUNT(*) as total FROM registrations r WHERE {where}
        )
        SELECT
            v.marca_nome,
            COUNT(r.id) as total,
            ROUND(COUNT(r.id) * 100.0 / totais.total, 2) as market_share_pct
        FROM registrations r
        JOIN vehicles v ON r.vehicle_id = v.id
        CROSS JOIN totais
        WHERE {where}
        GROUP BY v.marca_nome, totais.total
        ORDER BY total DESC
        LIMIT :top_n
    """)
    params["top_n"] = top_n

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, params)
        rows = result.fetchall()

    marcas = [
        {
            "marca": row.marca_nome,
            "total_emplacamentos": row.total,
            "market_share_pct": float(row.market_share_pct),
        }
        for row in rows
    ]
    return {"marcas": marcas, "ano": ano, "uf": uf, "count": len(marcas), "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    print(f"[FleetIntel MCP] Iniciando em modo {transport} na porta {MCP_PORT}")
    print(f"[FleetIntel MCP] Auth: {'habilitada' if settings.mcp_auth_token else 'desabilitada'}")
    mcp.run(transport=transport)
