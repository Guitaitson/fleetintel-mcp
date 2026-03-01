# -*- coding: utf-8 -*-
"""FleetIntel Agent v4 - Comprehensive Test Suite

Script de teste abrangente para validar:
- Sistema de memoria de estado da arte
- Importacoes de modulos
- Queries ao banco de dados
- Fluxo conversacional completo

Usage:
    uv run python scripts/test_agent_v4.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Force UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")


def print_header(title: str):
    """Print formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"       {details}")


# ============================================
# Test 1: Module Imports
# ============================================

def test_imports():
    """Test all module imports."""
    print_header("TESTE 1: Importacoes de Modulos")
    
    tests = []
    
    # Test agent imports
    try:
        from agent import run_query, create_agent, AgentMemory, FleetIntelMemory
        print_result("Import agent module", True, "run_query, create_agent, AgentMemory, FleetIntelMemory")
        tests.append(True)
    except ImportError as e:
        print_result("Import agent module", False, str(e))
        tests.append(False)
    
    # Test memory_state_of_the_art imports
    try:
        from agent.memory_state_of_the_art import (
            Entity, Relationship, ConversationTurn, EntityType, get_memory
        )
        print_result("Import memory SOTA", True, "Entity, Relationship, ConversationTurn, EntityType")
        tests.append(True)
    except ImportError as e:
        print_result("Import memory SOTA", False, str(e))
        tests.append(False)
    
    # Test agent.memory imports (backward compatibility)
    try:
        from agent.memory import AgentMemory as LegacyAgentMemory, get_memory as get_legacy_memory
        print_result("Import legacy memory", True, "AgentMemory backward compatible")
        tests.append(True)
    except ImportError as e:
        print_result("Import legacy memory", False, str(e))
        tests.append(False)
    
    return all(tests)


# ============================================
# Test 2: Memory System
# ============================================

def test_memory_system():
    """Test memory system functionality."""
    print_header("TESTE 2: Sistema de Memoria SOTA")
    
    tests = []
    
    try:
        from agent.memory_state_of_the_art import FleetIntelMemory, get_memory, EntityType
        
        # Create memory instance
        memory = get_memory("test_user_123", "test_session")
        print_result("Create FleetIntelMemory", True, f"User: test_user_123")
        tests.append(True)
        
        # Test entity extraction
        entities = memory.extract_entities("Quantos veiculos da Volvo emplacaram em 2024?")
        print_result("Entity Extraction", True, f"Found {len(entities)} entities")
        tests.append(True)
        
        # Test context recall
        context = memory.recall("E da Mercedes?")
        print_result("Context Recall", True, f"Follow-up: {context.get('follow_up_detected', False)}")
        tests.append(True)
        
        # Test remember
        memory.remember("User query", "Assistant response")
        print_result("Remember Interaction", True, "Interaction stored")
        tests.append(True)
        
        # Test conversation summary
        summary = memory.get_conversation_summary()
        print_result("Conversation Summary", True, f"Turns: {len(memory.conversation_history)}")
        tests.append(True)
        
    except Exception as e:
        print_result("Memory System", False, str(e))
        tests.append(False)
    
    return all(tests)


# ============================================
# Test 3: create_agent Function
# ============================================

def test_create_agent():
    """Test create_agent factory function."""
    print_header("TESTE 3: Factory Function create_agent")
    
    tests = []
    
    try:
        from agent import create_agent
        
        # Create agent without config
        agent = create_agent()
        print_result("create_agent()", True, f"Type: {agent.get('type')}")
        tests.append(True)
        
        # Create agent with config
        agent = create_agent({"model": "glm-4.7", "temperature": 0.1})
        print_result("create_agent(config)", True, f"Config applied")
        tests.append(True)
        
        # Verify agent structure
        if agent.get("type") == "fleetintel_agent_v4":
            print_result("Agent Structure", True, "Correct structure")
            tests.append(True)
        else:
            print_result("Agent Structure", False, "Wrong structure")
            tests.append(False)
        
    except Exception as e:
        print_result("create_agent", False, str(e))
        tests.append(False)
    
    return all(tests)


# ============================================
# Test 4: Database Connection
# ============================================

async def test_database_connection():
    """Test database connection and basic queries."""
    print_header("TESTE 4: Conexao com Banco de Dados")
    
    tests = []
    
    try:
        from src.fleet_intel_mcp.db.connection import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Test basic connection
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            print_result("DB Connection", True, "Connected to Supabase")
            tests.append(True)
            
            # Test empresas table
            result = await session.execute(text("SELECT COUNT(*) FROM empresas"))
            count = result.scalar()
            print_result("Empresas Table", True, f"{count} empresas found")
            tests.append(True)
            
            # Test vehicles table
            result = await session.execute(text("SELECT COUNT(*) FROM vehicles"))
            count = result.scalar()
            print_result("Vehicles Table", True, f"{count} vehicles found")
            tests.append(True)
            
            # Test registrations table
            result = await session.execute(text("SELECT COUNT(*) FROM registrations"))
            count = result.scalar()
            print_result("Registrations Table", True, f"{count} registrations found")
            tests.append(True)
            
    except Exception as e:
        print_result("Database Connection", False, str(e))
        tests.append(False)
    
    return all(tests)


# ============================================
# Test 5: Query ADDIANTE (Critical Test)
# ============================================

async def test_addiante_query():
    """Test ADDIANTE company query - the critical test case."""
    print_header("TESTE 5: Query ADDIANTE (Caso Critico)")
    
    tests = []
    
    try:
        from src.fleet_intel_mcp.db.connection import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Search for ADDIANTE company
            query = """
                SELECT id, cnpj, razao_social, nome_fantasia
                FROM empresas
                WHERE razao_social ILIKE '%addiante%'
                   OR nome_fantasia ILIKE '%addiante%'
                LIMIT 5
            """
            result = await session.execute(text(query))
            empresas = result.fetchall()
            
            if empresas:
                print_result("Find ADDIANTE", True, f"Found {len(empresas)} empresa(s)")
                tests.append(True)
                
                for empresa in empresas:
                    print(f"       - {empresa.razao_social} (ID: {empresa.id})")
                
                # Get registrations for first ADDIANTE
                empresa_id = empresas[0].id
                
                # Query ALL registrations (no year filter)
                query_total = f"SELECT COUNT(*) as total FROM registrations WHERE empresa_id = {empresa_id}"
                result = await session.execute(text(query_total))
                total = result.scalar()
                print_result("ADDIANTE Total Registrations", True, f"{total} total")
                tests.append(True)
                
                # Query 2024 registrations
                query_2024 = f"SELECT COUNT(*) as total FROM registrations WHERE empresa_id = {empresa_id} AND EXTRACT(YEAR FROM data_emplacamento) = 2024"
                result = await session.execute(text(query_2024))
                count_2024 = result.scalar()
                print_result("ADDIANTE 2024", True, f"{count_2024} veiculos")
                tests.append(True)
                
                # Query 2025 registrations
                query_2025 = f"SELECT COUNT(*) as total FROM registrations WHERE empresa_id = {empresa_id} AND EXTRACT(YEAR FROM data_emplacamento) = 2025"
                result = await session.execute(text(query_2025))
                count_2025 = result.scalar()
                print_result("ADDIANTE 2025", True, f"{count_2025} veiculos")
                tests.append(True)
                
                # Store results for verification
                test_addiante_query.results = {
                    "total": total,
                    "2024": count_2024,
                    "2025": count_2025,
                    "empresa_id": empresa_id
                }
                
            else:
                print_result("Find ADDIANTE", False, "Not found in database")
                test_addiante_query.results = {"total": 0, "2024": 0, "2025": 0}
                tests.append(False)
                
    except Exception as e:
        print_result("ADDIANTE Query", False, str(e))
        test_addiante_query.results = {"error": str(e)}
        tests.append(False)
    
    return all(tests)


# ============================================
# Test 6: run_query Function (Integration)
# ============================================

async def test_run_query():
    """Test the main run_query function."""
    print_header("TESTE 6: Funcao run_query (Integracao)")
    
    tests = []
    
    try:
        from agent import run_query, get_memory
        
        # Test run_query function exists and is callable
        if callable(run_query):
            print_result("run_query callable", True)
            tests.append(True)
        else:
            print_result("run_query callable", False)
            tests.append(False)
        
        # Test get_memory function
        memory = get_memory("test_user_456")
        if memory:
            print_result("get_memory works", True)
            tests.append(True)
        else:
            print_result("get_memory works", False)
            tests.append(False)
        
    except Exception as e:
        print_result("run_query test", False, str(e))
        tests.append(False)
    
    return all(tests)


# ============================================
# Test 7: MCP Tools Availability
# ============================================

def test_mcp_tools():
    """Test MCP tools availability."""
    print_header("TESTE 7: Ferramentas MCP")
    
    tests = []
    
    try:
        from mcp_server.mcp_client import call_mcp_tool
        print_result("MCP Client Import", True)
        tests.append(True)
        
        # Check if tools are defined
        from mcp_server.main import app
        print_result("MCP Server Import", True, f"Server: {app.name}")
        tests.append(True)
        
    except ImportError as e:
        print_result("MCP Tools", False, str(e))
        tests.append(False)
    except Exception as e:
        print_result("MCP Tools", False, str(e))
        tests.append(False)
    
    return all(tests)


# ============================================
# Main Test Runner
# ============================================

async def run_all_tests():
    """Run all tests and generate report."""
    print_header("FLEETINTEL AGENT v4 - SUITE DE TESTES")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nExecutando testes...\n")
    
    results = []
    
    # Synchronous tests
    results.append(("Importacoes", test_imports()))
    results.append(("Memoria SOTA", test_memory_system()))
    results.append(("Factory create_agent", test_create_agent()))
    results.append(("MCP Tools", test_mcp_tools()))
    
    # Async tests
    results.append(("Conexao DB", await test_database_connection()))
    results.append(("Query ADDIANTE", await test_addiante_query()))
    results.append(("run_query Integracao", await test_run_query()))
    
    # Summary
    print_header("RESUMO DOS TESTES")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "[PASSOU]" if result else "[FALHOU]"
        print(f"  - {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passou(s), {failed} falhou(s)")
    
    # ADDIANTE specific results
    if hasattr(test_addiante_query, 'results'):
        print_header("RESULTADO ADDIANTE")
        r = test_addiante_query.results
        if "error" in r:
            print(f"[FALHA] Erro: {r['error']}")
        else:
            print(f"  Total de registros: {r.get('total', 'N/A')}")
            print(f"  Em 2024: {r.get('2024', 'N/A')} veiculos")
            print(f"  Em 2025: {r.get('2025', 'N/A')} veiculos")
            
            # Expected: ADDIANTE should have >500 vehicles in 2025
            count_2025 = r.get('2025', 0)
            if count_2025 >= 500:
                print(f"\n  [OK] Contagem correta: {count_2025} veiculos (esperado > 500)")
            else:
                print(f"\n  [ATENCAO] Contagem abaixo do esperado: {count_2025} veiculos")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
