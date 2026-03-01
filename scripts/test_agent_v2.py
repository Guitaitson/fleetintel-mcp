"""Test script for FleetIntel Agent v2

Verifies that the agent and MCP tools are functioning correctly.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv(".env.local")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.mcp_client import call_mcp_tool


async def test_mcp_tools():
    """Test MCP tools directly."""
    print("=" * 60)
    print("Testing MCP Tools")
    print("=" * 60)

    # Test 1: get_stats
    print("\n1. Testing get_stats...")
    try:
        result = await call_mcp_tool("get_stats")
        stats = result.get('stats', {})
        print(f"   OK - Stats: marcas={stats.get('marcas')}, modelos={stats.get('modelos')}")
        print(f"         vehicles={stats.get('vehicles')}, empresas={stats.get('empresas')}")
        print(f"         registrations={stats.get('registrations')}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 2: count_empresa_registrations with "addiante"
    print("\n2. Testing count_empresa_registrations with 'addiante'...")
    try:
        result = await call_mcp_tool(
            "count_empresa_registrations",
            razao_social="addiante",
            nome_fantasia=None,
            ano=2025,
        )
        print(f"   Result keys: {result.keys()}")
        if result.get("ambiguous") and result.get("empresas"):
            print(f"   OK - Found {len(result['empresas'])} companies - ambiguous: {result['ambiguous']}")
            for emp in result.get("empresas", []):
                print(f"      - {emp.get('razao_social')} ({emp.get('cnpj')})")
        elif result.get("error"):
            print(f"   ERROR: {result.get('error')}")
            if result.get("suggestion"):
                print(f"   Suggestion: {result.get('suggestion')}")
        else:
            count = result.get("count", 0)
            empresa = result.get("empresas", [{}])[0]
            nome = empresa.get("nome_fantasia") or empresa.get("razao_social", "Unknown")
            print(f"   OK - Found: {nome} with {count} registrations")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: count_empresa_registrations with "radiante" (should find more)
    print("\n3. Testing count_empresa_registrations with 'radiante'...")
    try:
        result = await call_mcp_tool(
            "count_empresa_registrations",
            razao_social="radiante",
            nome_fantasia=None,
            ano=2025,
        )
        print(f"   Result keys: {result.keys()}")
        if result.get("ambiguous") and result.get("empresas"):
            print(f"   OK - Found {len(result['empresas'])} companies - ambiguous: {result['ambiguous']}")
            for emp in result.get("empresas", [])[:5]:
                print(f"      - {emp.get('razao_social')} ({emp.get('cnpj')})")
        elif result.get("count", 0) > 0:
            print(f"   OK - Found: {result['empresas'][0].get('razao_social')} with {result['count']} registrations")
        else:
            print(f"   Result: {result}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 4: top_empresas_by_registrations
    print("\n4. Testing top_empresas_by_registrations for 2025...")
    try:
        result = await call_mcp_tool(
            "top_empresas_by_registrations",
            ano=2025,
            top_n=5,
        )
        print(f"   Result keys: {result.keys()}")
        empresas = result.get("empresas", [])
        if empresas:
            print(f"   OK - Top 5 companies by registrations in 2025:")
            for emp in empresas:
                print(f"      - {emp.get('razao_social')}: {emp.get('total_registrations')} registrations")
        else:
            print(f"   Result: {result}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 5: search_vehicles (Volvo)
    print("\n5. Testing search_vehicles for Volvo...")
    try:
        result = await call_mcp_tool(
            "search_vehicles",
            marca="Volvo",
            limit=3,
        )
        print(f"   Result keys: {result.keys()}")
        vehicles = result.get("vehicles", [])
        print(f"   OK - Found {len(vehicles)} Volvo vehicles")
        for v in vehicles[:3]:
            print(f"      - {v.get('marca')} {v.get('modelo')} ({v.get('ano_fabricacao')})")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 6: search_company_online (Brave Search)
    print("\n6. Testing search_company_online...")
    try:
        result = await call_mcp_tool(
            "search_company_online",
            company_name="Adiante locadora",
            country="br",
        )
        print(f"   Result keys: {result.keys()}")
        if result.get("found_online"):
            print(f"   OK - Found online: {len(result.get('search_results', []))} results")
        else:
            print(f"   - Not found online: {result.get('message')}")
    except Exception as e:
        print(f"   ERROR: {e}")

    print("\n" + "=" * 60)
    print("MCP Tools Test Complete")
    print("=" * 60)


async def test_agent():
    """Test the LangGraph agent."""
    print("\n" + "=" * 60)
    print("Testing FleetIntel Agent")
    print("=" * 60)

    try:
        from agent.agent import run_query

        # Test query 1: "quantos caminhoes a Volvo emplacou em 2024?"
        query = "quantos caminhoes a Volvo emplacou em 2024?"
        print(f"\nQuery 1: {query}")
        print("\nProcessing...")

        result = await run_query(query, user_id="test_user")
        print(f"\nResult:\n{result}")

        # Test query 2: "quantos caminhoes a addiante comprou em 2025?"
        query2 = "quantos caminhoes a addiante comprou em 2025?"
        print(f"\n" + "=" * 60)
        print(f"\nQuery 2: {query2}")
        print("\nProcessing...")

        result2 = await run_query(query2, user_id="test_user")
        print(f"\nResult:\n{result2}")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


async def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("FLEETINTEL AGENT v2 - TEST SUITE")
    print("=" * 60)

    await test_mcp_tools()
    await test_agent()

    print("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
