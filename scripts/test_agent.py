#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for the LangGraph agent."""

import asyncio
import os

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

from agent.agent import run_query, get_llm, tools


async def test_agent():
    """Test the agent with various queries."""
    print("=" * 60)
    print("FleetIntel Agent Test")
    print("=" * 60)
    
    # Test 1: Simple query
    print("\n[Test 1] Estatisticas do banco:")
    try:
        result = await run_query("Quantos veiculos tem no banco?")
        print(f"Resposta: {result}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # Test 2: Query with year
    print("\n[Test 2] Veiculos por marca:")
    try:
        result = await run_query("Quantos veiculos da FIAT foram emplacados em 2024?")
        print(f"Resposta: {result}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # Test 3: Top empresas
    print("\n[Test 3] Empresas que mais emplacaram:")
    try:
        result = await run_query("Qual empresa mais emplacou caminhao em 2025?")
        print(f"Resposta: {result}")
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_agent())
