"""Test script for LangGraph Agent.

Run with: python agent/test_agent.py
"""

import asyncio
import sys
from datetime import datetime

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import run_query, get_stats, search_vehicles, search_registrations_count


async def test_get_stats():
    """Test get_stats tool."""
    print("\n" + "="*60)
    print("TEST: get_stats")
    print("="*60)
    
    result = await get_stats.ainvoke({})
    print(f"  Marcas: {result.get('marcas', 0)}")
    print(f"  Modelos: {result.get('modelos', 0)}")
    print(f"  Veiculos: {result.get('vehicles', 0):,}")
    print(f"  Empresas: {result.get('empresas', 0):,}")
    print(f"  Registrations: {result.get('registrations', 0):,}")
    
    return result


async def test_search_vehicles_by_brand(brand: str = "M.BENZ"):
    """Test search_vehicles with brand filter."""
    print("\n" + "="*60)
    print(f"TEST: search_vehicles (marca={brand})")
    print("="*60)
    
    result = await search_vehicles.ainvoke({"marca": brand, "limit": 5})
    print(f"  Encontrados: {result.get('count', 0)} veiculos")
    for v in result.get("vehicles", [])[:5]:
        print(f"    - {v['marca']} {v['modelo']} | {v['placa']} | {v['ano_fabricacao']}")
    
    return result


async def test_registration_stats():
    """Test registration statistics."""
    print("\n" + "="*60)
    print("TEST: registration_stats")
    print("="*60)
    
    # Get total registrations
    from agent.agent import search_registrations_count
    
    # Try without date filter first
    result = await search_registrations_count.ainvoke({})
    print(f"  Total registros: {result.get('count', 0):,}")
    
    return result


async def test_agent_query(query: str):
    """Test the agent with a natural language query."""
    print("\n" + "="*60)
    print(f"TEST: agent query: '{query}'")
    print("="*60)
    
    result = await run_query(query)
    print(f"  Resposta: {result}")
    
    return result


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FleetIntel LangGraph Agent - Tests")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    results = {}
    
    # Test 1: Get stats
    try:
        await test_get_stats()
        results["get_stats"] = "OK"
        print("\n[OK] get_stats completed")
    except Exception as e:
        print(f"\n[FAIL] get_stats: {e}")
        results["get_stats"] = f"ERROR: {e}"
    
    # Test 2: Search vehicles by brand
    try:
        await test_search_vehicles_by_brand("M.BENZ")
        results["search_vehicles"] = "OK"
        print("\n[OK] search_vehicles completed")
    except Exception as e:
        print(f"\n[FAIL] search_vehicles: {e}")
        results["search_vehicles"] = f"ERROR: {e}"
    
    # Test 3: Registration stats
    try:
        await test_registration_stats()
        results["registration_stats"] = "OK"
        print("\n[OK] registration_stats completed")
    except Exception as e:
        print(f"\n[FAIL] registration_stats: {e}")
        results["registration_stats"] = f"ERROR: {e}"
    
    # Test 4: Agent queries
    test_queries = [
        "Quantos veiculos estao cadastrados?",
        "Liste as estatisticas do banco de dados",
    ]
    
    for query in test_queries:
        try:
            await test_agent_query(query)
            results[f"agent_{query[:20]}"] = "OK"
            print(f"\n[OK] Agent query completed")
        except Exception as e:
            print(f"\n[FAIL] Agent query: {e}")
            results[f"agent_{query[:20]}"] = f"ERROR: {e}"
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    for test_name, result in results.items():
        if "ERROR" in str(result):
            print(f"  [X] {test_name}: FAILED")
            failed += 1
        else:
            print(f"  [OK] {test_name}: PASSED")
            passed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    print("="*60)
    print(f"Completed at: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
