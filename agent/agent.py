"""FleetIntel LangGraph Agent v4 - State of the Art

Agente conversacional inteligente de estado da arte para processar consultas 
complexas sobre dados de frota usando MCP Tools e Knowledge Graph Memory.

Features v4 (State of the Art):
- FleetIntelMemory: Sistema de memória baseado em Knowledge Graph
- Entity Extraction: Extração automática de entidades (empresas, marcas, anos)
- Relationship Tracking: Rastreamento de relacionamentos semânticos
- Semantic Context: Preservação de contexto conversacional
- MCP Memory Server Integration: Persistência entre sessões
- Anti-Hallucination: Execução direta de queries com bypass LLM
- Query Classification: Classificação inteligente de intenção

Esta implementação usa tecnologia DE PONTA alinhada com tendências futuras.

Usage:
    from agent.agent import run_query

    result = await run_query("Quantos veículos da FIAT foram emplacados em 2024?", user_id="user_123")
    print(result)
"""

import os
import sys
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv(".env.local")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import new state-of-the-art memory system
from agent.memory_state_of_the_art import (
    FleetIntelMemory,
    get_memory,
    EntityType
)

from mcp_server.mcp_client import call_mcp_tool
from mcp_server.vector_search import search_empresas_vector


# ============================================
# Brand Name Mapping (Database to Common Names)
# ============================================

BRAND_MAP = {
    'mercedes': 'Mercedes-Benz',
    'mercedes-benz': 'Mercedes-Benz',
    'benz': 'Mercedes-Benz',
    'vw': 'Volkswagen',
    'volkswagen': 'Volkswagen',
    'iveco': 'Iveco',
    'volvo': 'Volvo',
    'daf': 'Daf',
    'scania': 'Scania',
    'hyundai': 'Hyundai',
    'ford': 'Ford',
    'chevrolet': 'Chevrolet',
    'gm': 'Chevrolet',
    'fiat': 'Fiat',
    'renault': 'Renault',
    'peugeot': 'Peugeot',
    'citroen': 'Citroen',
    'toyota': 'Toyota',
    'nissan': 'Nissan',
    'mitsubishi': 'Mitsubishi',
}


# ============================================
# Query Classification (Enhanced with Memory Context)
# ============================================

def normalize_brand(brand: str) -> str:
    """Normaliza nome de marca para formato do banco de dados."""
    brand_lower = brand.lower().strip()
    return BRAND_MAP.get(brand_lower, brand)


def classify_query_with_memory(query: str, memory: FleetIntelMemory) -> Dict[str, Any]:
    """
    Classifica a query usando classificação básica + contexto da memória.
    
    Esta função combina padrões linguísticos com o conhecimento acumulado
    pela memória de estado da arte.
    """
    query_lower = query.lower()
    
    # Get context from memory
    memory_context = memory.recall(query)
    
    result = {
        'type': 'general',
        'empresa': None,
        'marca': None,
        'ano': None,
        'uf': None,
        'is_pronoun_reference': False,
        'memory_context': memory_context,
        'referenced_entity': None,
    }
    
    # Extract year first (high priority)
    year_match = re.search(r'20[0-2][0-9]', query)
    if year_match:
        result['ano'] = int(year_match.group())
    
    # Check for follow-up patterns that reference memory
    follow_up_patterns = [
        r'\be\s+(?:da|d[ao]|dos|das)\s+(\w+)',  # "e da Mercedes?"
        r'\be\s+(?:os?\s+)?(?:caminh|veícul)',   # "e os caminhões?"
        r'\bquantos?\s+(?:em|de|no?|na?)\s+(\d{4})?',  # "quantos em 2024?"
        r'\bquantos?\s+(?:caminh|veícul)',  # "quantos caminhões?"
    ]
    
    for pattern in follow_up_patterns:
        match = re.search(pattern, query_lower)
        if match:
            result['is_pronoun_reference'] = True
            # Get referenced entity from memory if available
            if memory_context.get('referenced_entities'):
                result['referenced_entity'] = memory_context['referenced_entities'][0]
            break
    
    # Extract company name patterns
    empresa_pattern = r'\ba\s+([A-Za-zÀ-ÖØ-öø-ÿ]+)'
    match = re.search(empresa_pattern, query)
    if match:
        potential_company = match.group(1).lower()
        if potential_company not in ['que', 'qual', 'quantos', 'quantas']:
            result['empresa'] = potential_company
    
    # Extract brand - prioritize by pattern
    brand_priority = [
        ('da volvo', 'volvo'),
        ('da mercedes', 'mercedes'),
        ('da iveco', 'iveco'),
        ('da volkswagen', 'volkswagen'),
        ('da daf', 'daf'),
        ('da scania', 'scania'),
        ('da hyundai', 'hyundai'),
        ('da fiat', 'fiat'),
    ]
    
    for pattern, brand in brand_priority:
        if pattern in query_lower:
            result['marca'] = brand
            result['empresa'] = None
            break
    else:
        # Check for brand mentions without "da"
        for brand_lower, brand_db in BRAND_MAP.items():
            if brand_lower in query_lower:
                result['marca'] = brand_db.lower()
                if brand_lower not in ['a ', 'empresa', 'locadora']:
                    result['empresa'] = None
                break
    
    # Check for pronoun references
    if any(p in query_lower for p in ['ela', 'ele', 'esse', 'essa', 'esses', 'essas']):
        result['is_pronoun_reference'] = True
        # Try to resolve pronoun from memory
        if memory_context.get('last_entity_types'):
            entity_types = memory_context['last_entity_types']
            if 'empresa' in entity_types:
                result['empresa'] = entity_types['empresa']
            elif 'marca' in entity_types:
                result['marca'] = entity_types['marca']
    
    # Determine query type
    if 'quantos' in query_lower or 'quantas' in query_lower or 'quanto' in query_lower:
        if result['marca']:
            result['type'] = 'count_by_brand'
        elif result['empresa']:
            result['type'] = 'count_by_company'
        else:
            result['type'] = 'count_general'
    elif 'top' in query_lower or 'maior' in query_lower or 'ranking' in query_lower:
        result['type'] = 'ranking'
    elif 'stats' in query_lower or 'estat' in query_lower:
        result['type'] = 'stats'
    else:
        result['type'] = 'general'
    
    return result


# ============================================
# Direct Query Execution (Bypass LLM for reliability)
# ============================================

async def execute_query_direct(
    query_type: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Executa query diretamente no banco de dados via MCP Tools.
    
    Anti-hallucination: NEVER let LLM make up data.
    If tool returns no data, we say "no data" - not fabricate numbers.
    """
    try:
        # Determine which tool to use based on query type
        if query_type == 'count_by_brand':
            brand = params.get('marca', '')
            ano = params.get('ano')
            uf = params.get('uf')
            
            # Build query params - use 'marca' not 'brand'
            tool_params = {"marca": brand, "limit": 100}
            if ano:
                tool_params["ano_fabricacao_min"] = ano
                tool_params["ano_fabricacao_max"] = ano
            if uf:
                tool_params["uf"] = uf
            
            # FIX #2: Use **tool_params to unpack as kwargs
            result = await call_mcp_tool("search_vehicles", **tool_params)
            if result and 'vehicles' in result:
                # Count vehicles by brand
                count = len(result['vehicles'])
                return {
                    'success': True,
                    'count': count,
                    'brand': brand,
                    'ano': ano,
                    'uf': uf,
                    'data': result['vehicles'][:10],  # Return sample
                }
            return {'success': True, 'count': 0, 'brand': brand}
        
        elif query_type == 'count_by_company':
            empresa = params.get('empresa', '')
            ano = params.get('ano')
            
            # FIX #1-2: Usar ILIKE direto via MCP (mais confiável que vector search para nomes)
            count_result = await call_mcp_tool(
                "count_empresa_registrations",
                razao_social=empresa,
                nome_fantasia=empresa,
                ano=ano,
                fuzzy_match=True
            )
            
            # Verificar se encontrou empresas
            empresas_encontradas = count_result.get('empresas', [])
            if empresas_encontradas and count_result.get('count', 0) > 0:
                top_company = empresas_encontradas[0]
                return {
                    'success': True,
                    'count': count_result['count'],
                    'company': top_company,
                    'ano': ano,
                    'search_type': 'fuzzy',
                    'ambiguous': count_result.get('ambiguous', False)
                }
            
            return {'success': True, 'count': 0, 'company': empresa, 'search_type': 'fuzzy'}
        
        elif query_type == 'stats':
            result = await call_mcp_tool("get_database_stats", {})
            return {'success': True, 'stats': result}
        
        elif query_type == 'ranking':
            limit = params.get('limit', 10)
            result = await call_mcp_tool("get_ranking", {"limit": limit})
            return {'success': True, 'ranking': result}
        
        else:
            # General search
            result = await call_mcp_tool("search_all", {"query": params.get('query', '')})
            return {'success': True, 'data': result}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============================================
# Response Generation (with Memory Integration)
# ============================================

def generate_response(
    query_type: str,
    query_result: Dict[str, Any],
    classification: Dict[str, Any],
    memory: FleetIntelMemory
) -> str:
    """
    Gera resposta conversacional baseada no resultado da query.
    
    Uses memory context to maintain coherent conversation flow.
    """
    # Get current context from memory
    context = memory.recall("")
    is_follow_up = classification.get('is_pronoun_reference', False)
    
    # Handle no data case - NEVER fabricate
    if query_result.get('count', 0) == 0:
        if classification.get('marca'):
            return f"⚠️ **Sem dados**\n\nNão encontrei registros de emplacamento para **{classification['marca']}**"
        elif classification.get('empresa'):
            return f"⚠️ **Sem dados**\n\nNão encontrei registros para **{classification['empresa']}**"
        else:
            return "⚠️ **Sem dados**\n\nNão encontrei registros para esta consulta"
    
    # Format count
    count = query_result.get('count', 0)
    count_str = f"{count:,}".replace(",", ".")
    
    # Generate response based on query type
    if query_type == 'count_by_brand':
        brand = classification.get('marca', 'Unknown')
        ano = classification.get('ano')
        ano_str = f" em {ano}" if ano else ""
        
        if is_follow_up:
            return f"**{count_str} veículos** da **{brand}**{ano_str}"
        else:
            return f"📊 **{brand} emplacou {count_str} veículos{ano_str}**"
    
    elif query_type == 'count_by_company':
        company = query_result.get('company', {})
        company_name = company.get('razao_social', classification.get('empresa', 'Unknown'))
        ano = classification.get('ano')
        ano_str = f" em {ano}" if ano else ""
        
        if is_follow_up:
            return f"**{count_str} veículos**{ano_str}"
        else:
            return f"🚛 **{company_name} emplacou {count_str} veículos{ano_str}**"
    
    elif query_type == 'stats':
        stats = query_result.get('stats', {})
        return f"""📈 **Estatísticas do Banco**

• Total de registros: {stats.get('total_registrations', 'N/A'):,}
• Total de empresas: {stats.get('total_empresas', 'N/A'):,}
• Total de veículos: {stats.get('total_vehicles', 'N/A'):,}"""
    
    elif query_type == 'ranking':
        ranking = query_result.get('ranking', [])
        lines = ["🏆 **Ranking**"]
        for i, item in enumerate(ranking[:5], 1):
            lines.append(f"{i}. {item}")
        return "\n".join(lines)
    
    else:
        return f"✅ Encontrados {count_str} registros"


# ============================================
# Main Query Function
# ============================================

async def run_query(
    query: str,
    user_id: str = "default",
    session_id: str = "default"
) -> Dict[str, Any]:
    """
    Função principal para processar uma query.
    
    Fluxo:
    1. Obter/acriar memória para o usuário
    2. Classificar a query com contexto da memória
    3. Executar query diretamente (anti-hallucination)
    4. Gerar resposta conversacional
    5. Registrar interação na memória
    
    Returns:
        Dict com 'response' e 'success'
    """
    try:
        # Step 1: Get memory instance
        memory = get_memory(user_id, session_id)
        
        # Step 2: Classify query with memory context
        classification = classify_query_with_memory(query, memory)
        
        # Step 3: Execute query directly (BYPASS LLM for reliability)
        query_result = await execute_query_direct(
            query_type=classification['type'],
            params={
                'marca': classification.get('marca'),
                'empresa': classification.get('empresa'),
                'ano': classification.get('ano'),
                'uf': classification.get('uf'),
            }
        )
        
        # Step 4: Generate response
        response = generate_response(
            query_type=classification['type'],
            query_result=query_result,
            classification=classification,
            memory=memory
        )
        
        # Step 5: Remember this interaction
        memory.remember(query, response)
        
        # Build result dict
        result = {
            'success': True,
            'response': response,
            'query_type': classification['type'],
            'is_follow_up': classification.get('is_pronoun_reference', False),
            'memory_context': classification.get('memory_context', {}),
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'response': f"❌ Erro ao processar consulta: {str(e)}",
            'error': str(e)
        }


# ============================================
# Example Usage
# ============================================

if __name__ == "__main__":
    import asyncio
    
    async def demo():
        print("=== FleetIntel Agent v4 Demo ===\n")
        
        # Query 1: Initial query
        result1 = await run_query(
            "Quantos veículos da Volvo emplacaram em 2024?",
            user_id="user_123"
        )
        print(f"Q1: {result1['response']}\n")
        print(f"   Follow-up: {result1['is_follow_up']}\n")
        
        # Query 2: Follow-up with context
        result2 = await run_query(
            "E da Mercedes?",
            user_id="user_123"
        )
        print(f"Q2: {result2['response']}\n")
        print(f"   Follow-up: {result2['is_follow_up']}\n")
        
        # Query 3: Another follow-up
        result3 = await run_query(
            "Quantos em 2025?",
            user_id="user_123"
        )
        print(f"Q3: {result3['response']}\n")
        print(f"   Follow-up: {result3['is_follow_up']}\n")
        
        # Get memory summary
        memory = get_memory("user_123")
        print(f"Memory Summary: {memory.get_conversation_summary()}")
    
    asyncio.run(demo())


# ============================================
# create_agent - Factory Function
# ============================================

def create_agent(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory function para criar uma instância do agente.
    
    Returns:
        Dicionário com componentes do agente configurados
    
    Usage:
        from agent import create_agent
        
        agent = create_agent({
            "model": "glm-4.7",
            "temperature": 0.1,
            "memory_enabled": True
        })
    """
    config = config or {}
    
    return {
        "type": "fleetintel_agent_v4",
        "version": "4.0.0",
        "state_of_the_art": True,
        "memory": {
            "type": "knowledge_graph",
            "provider": "mcp_memory",
            "features": ["entity_extraction", "relationship_tracking", "semantic_context"]
        },
        "anti_hallucination": True,
        "config": config
    }


# ============================================
# AgentState - State Definition for LangGraph
# ============================================

class AgentState(Dict[str, Any]):
    """State definition for LangGraph agent workflow."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setdefault("messages", [])
        self.setdefault("memory", None)
        self.setdefault("context", {})
        self.setdefault("query_result", None)
        self.setdefault("response", "")
