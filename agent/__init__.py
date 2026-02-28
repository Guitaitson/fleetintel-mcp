"""FleetIntel LangGraph Agent v4 - State of the Art

Agente conversacional de estado da arte para processar consultas sobre dados de frota.

Features:
- Sistema de memória Knowledge Graph
- Entity Extraction NLP
- Relationship Tracking
- Anti-Hallucination (execução direta)
- MCP Tools Integration

Usage:
    from agent import run_query, create_agent, AgentMemory

    result = await run_query("Quantos veículos da Volvo emplacaram em 2024?", user_id="user_123")
"""

from .agent import (
    run_query,
    create_agent,
    AgentState,
    get_memory,
)

from .memory import (
    AgentMemory,
    get_memory as get_agent_memory,
    get_user_context,
)

from .memory_state_of_the_art import (
    FleetIntelMemory,
    Entity,
    Relationship,
    ConversationTurn,
    EntityType,
    get_memory as get_fleet_memory,
)

__all__ = [
    # Main functions
    "run_query",
    "create_agent",
    "AgentState",
    
    # Memory systems
    "AgentMemory",
    "FleetIntelMemory",
    "get_memory",
    "get_agent_memory",
    "get_fleet_memory",
    "get_user_context",
    
    # Memory types
    "Entity",
    "Relationship",
    "ConversationTurn",
    "EntityType",
]
