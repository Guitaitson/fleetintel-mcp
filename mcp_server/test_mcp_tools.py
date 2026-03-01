"""Test script for MCP Server tools.

This script tests all MCP tools by simulating calls to the database.
Run with: python mcp_server/test_mcp_tools.py
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy import text

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fleet_intel_mcp.db.connection import AsyncSessionLocal


async def test_get_stats():
    """Test the get_stats tool."""
    print("\n" + "="*60)
    print("TEST: get_stats")
    print("="*60)
    
    queries = {
        "marcas": text("SELECT COUNT(*) FROM marcas"),
        "modelos": text("SELECT COUNT(*) FROM modelos"),
        "vehicles": text("SELECT COUNT(*) FROM vehicles"),
        "empresas": text("SELECT COUNT(*) FROM empresas"),
        "enderecos": text("SELECT COUNT(*) FROM enderecos"),
        "contatos": text("SELECT COUNT(*) FROM contatos"),
        "registrations": text("SELECT COUNT(*) FROM registrations"),
    }
    
    stats = {}
    async with AsyncSessionLocal() as session:
        for key, query in queries.items():
            try:
                result = await session.execute(query)
                stats[key] = result.scalar() or 0
                print(f"  {key}: {stats[key]:,}")
            except Exception as e:
                stats[key] = f"ERROR: {e}"
                print(f"  {key}: ERROR - {e}")
    
    return stats


async def test_search_vehicles(limit: int = 5):
    """Test the search_vehicles tool."""
    print("\n" + "="*60)
    print(f"TEST: search_vehicles (limit={limit})")
    print("="*60)
    
    query = text("""
        SELECT id, chassi, placa, marca_nome, modelo_nome, ano_fabricacao, ano_modelo
        FROM vehicles
        ORDER BY id
        LIMIT :limit
    """)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        for row in rows:
            print(f"  ID: {row.id} | {row.marca_nome} {row.modelo_nome} | {row.placa} | {row.ano_fabricacao}")
    
    return len(rows)


async def test_search_empresas(limit: int = 5):
    """Test the search_empresas tool."""
    print("\n" + "="*60)
    print(f"TEST: search_empresas (limit={limit})")
    print("="*60)
    
    query = text("""
        SELECT id, cnpj, razao_social, nome_fantasia, segmento_cliente
        FROM empresas
        ORDER BY id
        LIMIT :limit
    """)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        for row in rows:
            nome = row.nome_fantasia or row.razao_social or "N/A"
            print(f"  ID: {row.id} | CNPJ: {row.cnpj} | {nome[:40]}")
    
    return len(rows)


async def test_search_registrations(limit: int = 5):
    """Test the search_registrations tool."""
    print("\n" + "="*60)
    print(f"TEST: search_registrations (limit={limit})")
    print("="*60)
    
    query = text("""
        SELECT r.id, r.data_emplacamento, r.municipio_emplacamento, r.uf_emplacamento,
               r.preco, v.chassi, v.placa, v.marca_nome, v.modelo_nome
        FROM registrations r
        JOIN vehicles v ON r.vehicle_id = v.id
        ORDER BY r.id
        LIMIT :limit
    """)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        for row in rows:
            preco = row.preco if row.preco is not None else 0.0
            print(f"  ID: {row.id} | {row.data_emplacamento} | {row.uf_emplacamento} | "
                  f"{row.marca_nome} {row.modelo_nome} | {row.placa} | R$ {preco:,.2f}")
    
    return len(rows)


async def test_vehicle_filter(marca: str = "FIAT"):
    """Test vehicle search with brand filter."""
    print("\n" + "="*60)
    print(f"TEST: search_vehicles with brand filter (marca={marca})")
    print("="*60)
    
    query = text("""
        SELECT id, chassi, placa, marca_nome, modelo_nome, ano_fabricacao, ano_modelo
        FROM vehicles
        WHERE marca_nome ILIKE :marca
        ORDER BY id
        LIMIT 10
    """)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"marca": f"{marca}%"})
        rows = result.fetchall()
        
        print(f"  Found {len(rows)} vehicles:")
        for row in rows:
            print(f"    ID: {row.id} | {row.marca_nome} {row.modelo_nome} | {row.placa}")
    
    return len(rows)


async def test_registration_date_filter():
    """Test registration search with date filter."""
    print("\n" + "="*60)
    print("TEST: search_registrations with date filter (2024-01-01 to 2024-12-31)")
    print("="*60)
    
    query = text("""
        SELECT COUNT(*) as count
        FROM registrations
        WHERE data_emplacamento BETWEEN '2024-01-01' AND '2024-12-31'
    """)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        count = result.scalar()
        print(f"  Registrations in 2024: {count:,}")
    
    return count


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FleetIntel MCP Server - Tool Tests")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    results = {}
    
    # Test 1: Get stats
    try:
        results["get_stats"] = await test_get_stats()
        print("\n[OK] get_stats completed successfully")
    except Exception as e:
        print(f"\n[FAIL] get_stats FAILED: {e}")
        results["get_stats"] = {"error": str(e)}
    
    # Test 2: Search vehicles
    try:
        count = await test_search_vehicles(limit=5)
        results["search_vehicles"] = {"count": count, "status": "OK"}
        print(f"\n[OK] search_vehicles completed successfully ({count} results)")
    except Exception as e:
        print(f"\n[FAIL] search_vehicles FAILED: {e}")
        results["search_vehicles"] = {"error": str(e)}
    
    # Test 3: Search empresas
    try:
        count = await test_search_empresas(limit=5)
        results["search_empresas"] = {"count": count, "status": "OK"}
        print(f"\n[OK] search_empresas completed successfully ({count} results)")
    except Exception as e:
        print(f"\n[FAIL] search_empresas FAILED: {e}")
        results["search_empresas"] = {"error": str(e)}
    
    # Test 4: Search registrations
    try:
        count = await test_search_registrations(limit=5)
        results["search_registrations"] = {"count": count, "status": "OK"}
        print(f"\n[OK] search_registrations completed successfully ({count} results)")
    except Exception as e:
        print(f"\n[FAIL] search_registrations FAILED: {e}")
        results["search_registrations"] = {"error": str(e)}
    
    # Test 5: Vehicle filter
    try:
        count = await test_vehicle_filter(marca="FIAT")
        results["vehicle_filter"] = {"count": count, "status": "OK"}
        print(f"\n[OK] vehicle_filter completed successfully ({count} results)")
    except Exception as e:
        print(f"\n[FAIL] vehicle_filter FAILED: {e}")
        results["vehicle_filter"] = {"error": str(e)}
    
    # Test 6: Registration date filter
    try:
        count = await test_registration_date_filter()
        results["registration_date_filter"] = {"count": count, "status": "OK"}
        print(f"\n[OK] registration_date_filter completed successfully")
    except Exception as e:
        print(f"\n[FAIL] registration_date_filter FAILED: {e}")
        results["registration_date_filter"] = {"error": str(e)}
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if isinstance(result, dict) and "error" in result:
            print(f"  [X] {test_name}: FAILED")
        else:
            print(f"  [OK] {test_name}: PASSED")
    
    print("\n" + "="*60)
    print(f"Completed at: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    return 0 if all("error" not in r for r in results.values()) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
