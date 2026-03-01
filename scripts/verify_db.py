#!/usr/bin/env python
"""Verify if empresas exist in the database."""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.mcp_client import call_mcp_tool


async def verify_database():
    results = {}
    
    # Test 1: Search for "adiante"
    print("1. Buscando 'adiante'...")
    result = await call_mcp_tool(
        "count_empresa_registrations",
        razao_social="adiante",
        nome_fantasia="adiante",
        fuzzy_match=True
    )
    results["adiante"] = {
        "count": result.get("count"),
        "empresas": result.get("empresas", [])[:3],
        "ambiguous": result.get("ambiguous"),
    }
    
    # Test 2: Search for "locadora"
    print("2. Buscando 'locadora'...")
    result2 = await call_mcp_tool(
        "count_empresa_registrations",
        razao_social="locadora",
        nome_fantasia="locadora",
        fuzzy_match=True
    )
    results["locadora"] = {
        "count": result2.get("count"),
        "empresas": result2.get("empresas", [])[:3],
        "ambiguous": result2.get("ambiguous"),
    }
    
    # Test 3: Search for "volvo" vehicles
    print("3. Buscando 'volvo'...")
    result3 = await call_mcp_tool(
        "search_vehicles",
        brand="volvo",
        ano=2024
    )
    results["volvo"] = {
        "vehicles_count": len(result3.get("vehicles", [])),
        "sample": result3.get("vehicles", [{}])[0] if result3.get("vehicles") else {},
    }
    
    # Save to file
    output_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "db_verify_results.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(verify_database())
