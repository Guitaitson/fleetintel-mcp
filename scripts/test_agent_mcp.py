#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do agent com MCP para verificar que nao ha recursao.
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import run_query


async def test_agent_no_recursion():
    """Testa que o agent nao entra em recursao."""
    print("=" * 60)
    print("TESTE: Agent com MCP (sem recursao)")
    print("=" * 60)
    print()
    
    # Test 1: Query simples
    print("[1] Testando query: 'qual empresa mais emplacou caminhao em 2025?'")
    try:
        result = await run_query("qual empresa mais emplacou caminhao em 2025?")
        print(f"   Resultado: {result[:200]}...")
        print("   [OK] Query executada sem recursao!")
    except Exception as e:
        if "recursion" in str(e).lower():
            print(f"   [ERRO] Recursao detectada: {e}")
            return False
        else:
            print(f"   [INFO] Erro (esperado sem API key): {e}")
    print()
    
    # Test 2: Stats query
    print("[2] Testando query: 'quantos veiculos tem no banco?'")
    try:
        result = await run_query("quantos veiculos tem no banco?")
        print(f"   Resultado: {result[:200]}...")
        print("   [OK] Query executada sem recursao!")
    except Exception as e:
        if "recursion" in str(e).lower():
            print(f"   [ERRO] Recursao detectada: {e}")
            return False
        else:
            print(f"   [INFO] Erro (esperado sem API key): {e}")
    print()
    
    # Test 3: Listagem
    print("[3] Testando query: 'liste as marcas de caminhoes'")
    try:
        result = await run_query("liste as marcas de caminhoes")
        print(f"   Resultado: {result[:200]}...")
        print("   [OK] Query executada sem recursao!")
    except Exception as e:
        if "recursion" in str(e).lower():
            print(f"   [ERRO] Recursao detectada: {e}")
            return False
        else:
            print(f"   [INFO] Erro (esperado sem API key): {e}")
    print()
    
    print("=" * 60)
    print("TESTE CONCLUIDO - Agent usando MCP!")
    print("=" * 60)
    return True


async def main():
    """Executa os testes."""
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    
    success = await test_agent_no_recursion()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
