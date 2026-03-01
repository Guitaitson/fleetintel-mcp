"""Test script for count_empresa_registrations tool"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_count_empresa_registrations():
    """Test the count_empresa_registrations tool directly."""
    from mcp_server.mcp_client import MCPClient
    
    client = MCPClient()
    
    print("Testing count_empresa_registrations...")
    print("=" * 50)
    
    # Test 1: Search for "Adiante"
    print("\n1. Searching for empresa 'Adiante':")
    try:
        result = await client._search_empresas(
            razao_social="Adiante",
            limit=5
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Count registrations for Adiante in 2025
    print("\n2. Counting registrations for Adiante in 2025:")
    try:
        result = await client._count_empresa_registrations(
            razao_social="Adiante",
            ano=2025
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Using call_mcp_tool wrapper
    print("\n3. Using call_mcp_tool wrapper:")
    from mcp_server.mcp_client import call_mcp_tool
    try:
        result = await call_mcp_tool(
            "count_empresa_registrations",
            razao_social="Adiante",
            ano=2025
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_count_empresa_registrations())
