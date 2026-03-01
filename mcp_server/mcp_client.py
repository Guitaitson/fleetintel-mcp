"""MCP Client for LangGraph Agent

Provides a simple interface for the LangGraph agent to call MCP tools
without duplicating SQL queries.

Usage:
    from mcp_server.mcp_client import MCPClient
    
    client = MCPClient()
    result = await client.call_tool("search_vehicles", marca="FIAT")
"""

import asyncio
import os
import sys
from typing import Any, Optional
from datetime import datetime, date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.fleet_intel_mcp.db.connection import AsyncSessionLocal


class MCPClient:
    """
    Client for calling MCP tools from the LangGraph agent.
    
    This client provides direct access to the MCP tool implementations,
    allowing the agent to use pre-defined queries without duplicating SQL.
    """
    
    def __init__(self):
        """Initialize the MCP client."""
        pass
    
    async def call_tool(self, tool_name: str, **kwargs) -> dict:
        """
        Call an MCP tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            dict: Result from the tool execution
        """
        if tool_name == "get_stats":
            return await self._get_stats()
        elif tool_name == "search_vehicles":
            return await self._search_vehicles(**kwargs)
        elif tool_name == "search_empresas":
            return await self._search_empresas(**kwargs)
        elif tool_name == "search_registrations":
            return await self._search_registrations(**kwargs)
        elif tool_name == "top_empresas_by_registrations":
            return await self._top_empresas_by_registrations(**kwargs)
        elif tool_name == "count_empresa_registrations":
            return await self._count_empresa_registrations(**kwargs)
        elif tool_name == "search_company_online":
            return await self._search_company_online(**kwargs)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _get_stats(self) -> dict:
        """Get database statistics."""
        queries = {
            "marcas": "SELECT COUNT(*) FROM marcas",
            "modelos": "SELECT COUNT(*) FROM modelos",
            "vehicles": "SELECT COUNT(*) FROM vehicles",
            "empresas": "SELECT COUNT(*) FROM empresas",
            "enderecos": "SELECT COUNT(*) FROM enderecos",
            "contatos": "SELECT COUNT(*) FROM contatos",
            "registrations": "SELECT COUNT(*) FROM registrations",
        }
        
        stats = {}
        async with AsyncSessionLocal() as session:
            for key, query in queries.items():
                result = await session.execute(text(query))
                stats[key] = result.scalar() or 0
        
        return {
            "stats": stats,
            "count": len(stats),
            "query": "get_stats",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _search_vehicles(
        self,
        chassi: Optional[str] = None,
        placa: Optional[str] = None,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
        ano_fabricacao_min: Optional[int] = None,
        ano_fabricacao_max: Optional[int] = None,
        limit: int = 100,
    ) -> dict:
        """Search for vehicles."""
        conditions = []
        params = {"limit": limit}
        
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
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = text(f"""
            SELECT id, chassi, placa, marca_nome, modelo_nome, ano_fabricacao, ano_modelo
            FROM vehicles
            WHERE {where_clause}
            ORDER BY id
            LIMIT :limit
        """)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(query, params)
            rows = result.fetchall()
            vehicles = [
                {
                    "id": row.id,
                    "chassi": row.chassi,
                    "placa": row.placa,
                    "marca": row.marca_nome,
                    "modelo": row.modelo_nome,
                    "ano_fabricacao": row.ano_fabricacao,
                    "ano_modelo": row.ano_modelo,
                }
                for row in rows
            ]
        
        return {
            "vehicles": vehicles,
            "count": len(vehicles),
            "query": "search_vehicles",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _search_empresas(
        self,
        cnpj: Optional[str] = None,
        razao_social: Optional[str] = None,
        nome_fantasia: Optional[str] = None,
        segmento_cliente: Optional[str] = None,
        grupo_locadora: Optional[str] = None,
        query: Optional[str] = None,  # Generic search query
        limit: int = 100,
    ) -> dict:
        """Search for companies."""
        conditions = []
        params = {"limit": limit}
        
        # Generic query searches all text fields
        if query:
            conditions.append(
                "(razao_social ILIKE :query OR nome_fantasia ILIKE :query OR "
                "segmento_cliente ILIKE :query OR grupo_locadora ILIKE :query)"
            )
            params["query"] = f"%{query}%"
        else:
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
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query_sql = text(f"""
            SELECT id, cnpj, razao_social, nome_fantasia, segmento_cliente, grupo_locadora
            FROM empresas
            WHERE {where_clause}
            ORDER BY id
            LIMIT :limit
        """)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, params)
            rows = result.fetchall()
            empresas = [
                {
                    "id": row.id,
                    "cnpj": row.cnpj,
                    "razao_social": row.razao_social,
                    "nome_fantasia": row.nome_fantasia,
                    "segmento_cliente": row.segmento_cliente,
                    "grupo_locadora": row.grupo_locadora,
                }
                for row in rows
            ]
        
        return {
            "empresas": empresas,
            "count": len(empresas),
            "query": "search_empresas",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _search_registrations(
        self,
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
        """Search for registrations."""
        conditions = []
        params = {"limit": limit}
        
        if data_emplacamento_inicio:
            conditions.append("r.data_emplacamento >= :data_inicio")
            # Convert string date to date object for asyncpg
            params["data_inicio"] = date.fromisoformat(data_emplacamento_inicio) if isinstance(data_emplacamento_inicio, str) else data_emplacamento_inicio
        if data_emplacamento_fim:
            conditions.append("r.data_emplacamento <= :data_fim")
            # Convert string date to date object for asyncpg
            params["data_fim"] = date.fromisoformat(data_emplacamento_fim) if isinstance(data_emplacamento_fim, str) else data_emplacamento_fim
        if municipio_emplacamento:
            conditions.append("r.municipio_emplacamento ILIKE :municipio")
            params["municipio"] = f"%{municipio_emplacamento}%"
        if uf_emplacamento:
            conditions.append("r.uf_emplacamento = :uf")
            params["uf"] = uf_emplacamento
        if preco_min:
            conditions.append("r.preco >= :preco_min")
            params["preco_min"] = preco_min
        if preco_max:
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
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = text(f"""
            SELECT r.id, r.data_emplacamento, r.municipio_emplacamento, r.uf_emplacamento,
                   r.preco, r.preco_validado, v.chassi, v.placa, v.marca_nome, v.modelo_nome,
                   v.ano_fabricacao, v.ano_modelo, e.cnpj, e.razao_social, e.nome_fantasia,
                   e.segmento_cliente, e.grupo_locadora
            FROM registrations r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN empresas e ON r.empresa_id = e.id
            WHERE {where_clause}
            ORDER BY r.id
            LIMIT :limit
        """)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(query, params)
            rows = result.fetchall()
            registrations = [
                {
                    "id": row.id,
                    "data_emplacamento": str(row.data_emplacamento),
                    "municipio": row.municipio_emplacamento,
                    "uf": row.uf_emplacamento,
                    "preco": row.preco,
                    "preco_validado": row.preco_validado,
                    "chassi": row.chassi,
                    "placa": row.placa,
                    "marca": row.marca_nome,
                    "modelo": row.modelo_nome,
                    "ano_fabricacao": row.ano_fabricacao,
                    "ano_modelo": row.ano_modelo,
                    "cnpj": row.cnpj,
                    "razao_social": row.razao_social,
                    "nome_fantasia": row.nome_fantasia,
                    "segmento_cliente": row.segmento_cliente,
                    "grupo_locadora": row.grupo_locadora,
                }
                for row in rows
            ]
        
        return {
            "registrations": registrations,
            "count": len(registrations),
            "query": "search_registrations",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _top_empresas_by_registrations(
        self,
        ano: int,
        uf: Optional[str] = None,
        top_n: int = 10,
    ) -> dict:
        """Get top N companies by registrations."""
        conditions = ["EXTRACT(YEAR FROM r.data_emplacamento) = :ano"]
        params = {"ano": ano, "top_n": top_n}
        
        if uf:
            conditions.append("r.uf_emplacamento = :uf")
            params["uf"] = uf
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT e.id, e.razao_social, e.nome_fantasia, e.segmento_cliente,
                   COUNT(r.id) as total_registrations, SUM(r.preco) as total_valor
            FROM empresas e
            JOIN registrations r ON e.id = r.empresa_id
            WHERE {where_clause}
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
                    "total_valor": float(row.total_valor) if row.total_valor else 0,
                }
                for row in rows
            ]
        
        return {
            "empresas": empresas,
            "count": len(empresas),
            "query": "top_empresas_by_registrations",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _count_empresa_registrations(
        self,
        razao_social: Optional[str] = None,
        nome_fantasia: Optional[str] = None,
        ano: Optional[int] = None,
        fuzzy_match: bool = True,
    ) -> dict:
        """Count vehicle registrations for a specific company by name and year.
        
        Supports fuzzy matching and returns multiple companies if there are ambiguities.
        """
        # First, search for matching empresas with fuzzy matching
        conditions = []
        params = {"limit": 10}  # Get more results for disambiguation
        
        if razao_social:
            if fuzzy_match:
                # Try multiple variations for fuzzy matching
                conditions.append("(razao_social ILIKE :razao_social OR nome_fantasia ILIKE :razao_social)")
                params["razao_social"] = f"%{razao_social}%"
            else:
                conditions.append("razao_social ILIKE :razao_social")
                params["razao_social"] = f"%{razao_social}%"
        if nome_fantasia:
            conditions.append("nome_fantasia ILIKE :nome_fantasia")
            params["nome_fantasia"] = f"%{nome_fantasia}%"
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        empresa_query = text(f"""
            SELECT id, cnpj, razao_social, nome_fantasia, segmento_cliente, grupo_locadora
            FROM empresas
            WHERE {where_clause}
            ORDER BY id
            LIMIT :limit
        """)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(empresa_query, params)
            empresas = result.fetchall()
            
            if not empresas:
                return {
                    "count": 0,
                    "empresas": [],
                    "ambiguous": False,
                    "error": "Empresa não encontrada",
                    "suggestion": "Tente buscar por CNPJ ou parte do nome",
                    "query": "count_empresa_registrations",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # If multiple empresas found, check if they are related (same base name)
            if len(empresas) > 1:
                # Check if they share similar names (could be same company with different CNPJs)
                base_names = set()
                for emp in empresas:
                    # Normalize name for comparison
                    name = emp.razao_social.lower().replace("ltda", "").replace("sa", "").replace(" ", "").strip()
                    base_names.add(name[:20])  # First 20 chars as base identifier
                
                # If all have similar base, treat as same company
                is_related = len(base_names) == 1
                
                return {
                    "count": 0,  # Will be calculated below
                    "empresas": [
                        {
                            "id": emp.id,
                            "cnpj": emp.cnpj,
                            "razao_social": emp.razao_social,
                            "nome_fantasia": emp.nome_fantasia,
                            "segmento_cliente": emp.segmento_cliente,
                            "grupo_locadora": emp.grupo_locadora,
                        }
                        for emp in empresas
                    ],
                    "ambiguous": not is_related,
                    "is_related": is_related,
                    "message": f"{len(empresas)} empresas encontradas" + (" (tratadas como mesma empresa)" if is_related else " - qual você quer dizer?"),
                    "query": "count_empresa_registrations",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Single empresa found
            empresa = empresas[0]
            empresa_id = empresa.id
            
            # Now count registrations
            if ano:
                count_query = text("""
                    SELECT COUNT(*) as count
                    FROM registrations r
                    WHERE r.empresa_id = :empresa_id
                    AND EXTRACT(YEAR FROM r.data_emplacamento) = :ano
                """)
                count_params = {"empresa_id": empresa_id, "ano": ano}
            else:
                count_query = text("""
                    SELECT COUNT(*) as count
                    FROM registrations r
                    WHERE r.empresa_id = :empresa_id
                """)
                count_params = {"empresa_id": empresa_id}
            
            result = await session.execute(count_query, count_params)
            count = result.scalar() or 0
            
            return {
                "count": count,
                "empresas": [{
                    "id": empresa.id,
                    "cnpj": empresa.cnpj,
                    "razao_social": empresa.razao_social,
                    "nome_fantasia": empresa.nome_fantasia,
                    "segmento_cliente": empresa.segmento_cliente,
                    "grupo_locadora": empresa.grupo_locadora,
                }],
                "ambiguous": False,
                "is_related": False,
                "ano": ano,
                "query": "count_empresa_registrations",
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _search_company_online(
        self,
        company_name: str,
        country: str = "br",
    ) -> dict:
        """Search for a company online using Brave Search MCP."""
        try:
            # Use global Brave Search MCP function
            from mcp__brave___search import brave_web_search
            
            query = f"{company_name} empresa CNPJ Brasil locadora frota"
            results = await brave_web_search(query=query, count=5)
            
            if results and len(results) > 0:
                # Extract results
                search_results = []
                for r in results:
                    search_results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "description": r.get("description", "")[:200] if r.get("description") else "",
                    })
                
                return {
                    "company_name": company_name,
                    "search_results": search_results,
                    "found_online": True,
                    "query": "search_company_online",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "company_name": company_name,
                    "search_results": [],
                    "found_online": False,
                    "message": "No results found online",
                    "query": "search_company_online",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except ImportError as e:
            return {
                "company_name": company_name,
                "search_results": [],
                "found_online": False,
                "message": f"Brave Search MCP not available: {e}",
                "suggestion": "Try searching with different keywords in the local database.",
                "query": "search_company_online",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "company_name": company_name,
                "error": str(e),
                "query": "search_company_online",
                "timestamp": datetime.utcnow().isoformat(),
            }


# Singleton instance
_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create the MCP client singleton."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client


# Convenience functions for LangGraph tools
async def call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """Convenience function to call an MCP tool."""
    client = get_mcp_client()
    return await client.call_tool(tool_name, **kwargs)
