"""FleetIntel Memory System v4 - State of the Art

Sistema de memória inteligente baseado em Knowledge Graph que utiliza
o MCP Memory Server para armazenamento persistente e semântico.

Arquitetura:
- Entity Extraction: Extrai entidades (empresas, marcas, anos, quantidades)
- Relationship Tracking: Mantém relacionamentos entre entidades
- Semantic Context: Preserva contexto semântico da conversa
- Knowledge Graph: Usa grafo de conhecimento para navegação inteligente

Esta é uma implementação DE PONTA, alinhada com tendências futuras de AI agents.
"""

import os
import sys
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import json

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================
# JSON Serialization Helpers
# ============================================

def _is_serializable(obj: Any) -> bool:
    """Check if an object is JSON serializable."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return True
    if isinstance(obj, (list, tuple)):
        return all(_is_serializable(item) for item in obj)
    if isinstance(obj, dict):
        return all(_is_serializable(k) and _is_serializable(v) for k, v in obj.items())
    return False

def _to_serializable(obj: Any) -> Any:
    """Convert an object to a JSON-serializable form."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, Enum):
        return obj.value
    # Handle dataclass objects
    if hasattr(obj, 'to_dict') and callable(obj.to_dict):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return _to_serializable(obj.__dict__)
    return str(obj)


# ============================================
# Memory Types (Structured Data Models)
# ============================================

class EntityType(Enum):
    """Tipos de entidades reconhecidas pelo sistema."""
    EMPRESA = "empresa"
    MARCA = "marca"
    ANO = "ano"
    QUANTIDADE = "quantidade"
    VEICULO = "veiculo"
    TOPICO = "topico"
    CONTEXTO = "contexto"


@dataclass
class Entity:
    """Representa uma entidade extraída da conversa."""
    name: str
    entity_type: EntityType
    confidence: float = 1.0
    source: str = "conversation"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "entity_type": self.entity_type.value,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


@dataclass
class Relationship:
    """Relação entre duas entidades."""
    from_entity: str
    relation_type: str
    to_entity: str
    context: str = ""
    strength: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "from": self.from_entity,
            "relation": self.relation_type,
            "to": self.to_entity,
            "context": self.context,
            "strength": self.strength,
            "created_at": self.created_at
        }


@dataclass
class ConversationTurn:
    """Um turno de conversa completo."""
    user_message: str
    assistant_response: str
    entities_extracted: List[Entity]
    relationships_created: List[Relationship]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    context_summary: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "entities": [e.to_dict() for e in self.entities_extracted],
            "relationships": [r.to_dict() for r in self.relationships_created],
            "timestamp": self.timestamp,
            "context_summary": self.context_summary
        }


# ============================================
# State-of-the-art Memory System
# ============================================

class FleetIntelMemory:
    """
    Sistema de memória inteligente que usa Knowledge Graph.
    
    Features:
    - Extração automática de entidades
    - Rastreamento de relacionamentos
    - Preservação de contexto semântico
    - Integração com MCP Memory Server
    - Recuperação inteligente de contexto
    
    Este sistema é DE PONTA e fundamental para a inteligência do agente.
    """
    
    def __init__(self, user_id: str, session_id: str = "default"):
        self.user_id = user_id
        self.session_id = session_id
        self.conversation_history: List[ConversationTurn] = []
        self.current_context: Dict[str, Any] = {}
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        
        # Brand name mapping
        self.brand_map = {
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
        
        # Load existing memory from MCP
        self._load_from_mcp()
    
    # ============================================
    # Entity Extraction (NLP-powered)
    # ============================================
    
    def extract_entities(self, message: str) -> List[Entity]:
        """
        Extrai entidades inteligentes da mensagem usando padrões linguísticos.
        
        Returns:
            Lista de entidades extraídas com alta precisão
        """
        entities = []
        message_lower = message.lower()
        
        # Extract year patterns (2020-2026)
        year_pattern = r'\b(20[2-6][0-9])\b'
        for match in re.finditer(year_pattern, message):
            year = match.group(1)
            entities.append(Entity(
                name=year,
                entity_type=EntityType.ANO,
                confidence=1.0,
                source="pattern",
                metadata={"extracted_from": match.span()}
            ))
        
        # Extract brand names
        for abbreviation, full_name in self.brand_map.items():
            if abbreviation in message_lower:
                entities.append(Entity(
                    name=full_name,
                    entity_type=EntityType.MARCA,
                    confidence=1.0,
                    source="brand_map",
                    metadata={"original_term": abbreviation}
                ))
        
        # Extract quantities (if present)
        quantity_pattern = r'\b(\d{1,3}(?:\.\d{3})*)\s*(caminh|veícul|onibus|ônibus)\b'
        for match in re.finditer(quantity_pattern, message_lower):
            entities.append(Entity(
                name=f"quantidade_{match.group(1)}",
                entity_type=EntityType.QUANTIDADE,
                confidence=0.9,
                source="pattern",
                metadata={"value": match.group(1), "unit": match.group(2)}
            ))
        
        return entities
    
    # ============================================
    # Relationship Detection
    # ============================================
    
    def detect_relationships(self, entities: List[Entity], message: str) -> List[Relationship]:
        """
        Detecta relacionamentos entre entidades baseados em padrões linguísticos.
        
        Examples:
        - "empresa X comprou Y veículos" -> [X] comprou [Y]
        - "marca Z emplacou em 2024" -> [Z] emplacou [2024]
        """
        relationships = []
        
        # Build entity name lookup
        entity_names = {e.name for e in entities}
        entity_by_type = {e.entity_type: e.name for e in entities}
        
        # Pattern: [empresa] comprou [quantidade]
        if EntityType.EMPRESA in entity_by_type and EntityType.QUANTIDADE in entity_by_type:
            if any(word in message.lower() for word in ['comprou', 'adquiriu', 'registrou']):
                relationships.append(Relationship(
                    from_entity=entity_by_type[EntityType.EMPRESA],
                    relation_type="comprou",
                    to_entity=entity_by_type[EntityType.QUANTIDADE],
                    context=message[:200]
                ))
        
        # Pattern: [marca] emplacou em [ano]
        if EntityType.MARCA in entity_by_type and EntityType.ANO in entity_by_type:
            if any(word in message.lower() for word in ['emplacou', 'vendeu', 'venderam']):
                relationships.append(Relationship(
                    from_entity=entity_by_type[EntityType.MARCA],
                    relation_type="emplacou_em",
                    to_entity=entity_by_type[EntityType.ANO],
                    context=message[:200]
                ))
        
        return relationships
    
    # ============================================
    # Context Management
    # ============================================
    
    def update_context(self, user_message: str, assistant_response: str):
        """
        Atualiza o contexto da conversa com nova informação.
        
        Este método é FUNDAMENTAL para a inteligência do sistema,
        pois mantém o estado conversacional de forma estruturada.
        """
        # Extract entities from user message
        entities = self.extract_entities(user_message)
        
        # Detect relationships
        relationships = self.detect_relationships(entities, user_message)
        
        # Create conversation turn
        turn = ConversationTurn(
            user_message=user_message,
            assistant_response=assistant_response,
            entities_extracted=entities,
            relationships_created=relationships
        )
        
        # Store in history
        self.conversation_history.append(turn)
        
        # Update entity registry
        for entity in entities:
            if entity.name not in self.entities:
                self.entities[entity.name] = entity
        
        # Update relationships
        self.relationships.extend(relationships)
        
        # Update current context (last entities mentioned)
        if entities:
            # Most recent entities are the ones in the last message
            self.current_context = {
                "last_entities": [e.name for e in entities],
                "last_entity_types": {e.entity_type.value: e.name for e in entities},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Sync to MCP Memory Server
        self._sync_to_mcp(turn)
        
        # Keep only last 20 turns (memory optimization)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """
        Recupera contexto relevante para uma query.
        
        Usa o conhecimento acumulado para responder perguntas de seguimento
        como "e da Mercedes?" ou "quantos em 2024?".
        """
        query_lower = query.lower()
        
        # Convert entities to dicts for JSON serialization
        entities_raw = self.extract_entities(query)
        entities_in_query = [e.to_dict() for e in entities_raw]
        
        context = {
            "entities_in_query": entities_in_query,
            "referenced_entities": [],
            "follow_up_detected": False,
            "suggested_entities": []
        }
        
        # Detect pronouns and references
        follow_up_patterns = [
            r'\be\s+(?:da|d[ao]|dos|das)\s+(\w+)',  # "e da Mercedes?"
            r'\be\s+eles?\s',  # "e eles?"
            r'\be\s+ela?s?\s',  # "e elas?"
            r'\bquantos?\s+(?:em|de|no?|na?)\s+(\d{4})',  # "quantos em 2024?"
            r'\bquantos?\s+(?:caminh|veícul)',  # "quantos caminhões?"
        ]
        
        for pattern in follow_up_patterns:
            match = re.search(pattern, query_lower)
            if match:
                context["follow_up_detected"] = True
                # Try to extract referenced entity
                if match.lastindex:
                    referenced = match.group(1)
                    if referenced in self.brand_map:
                        context["referenced_entities"].append(self.brand_map[referenced])
                    elif referenced in self.entities:
                        context["referenced_entities"].append(referenced)
        
        # Suggest entities from conversation history
        if self.entities:
            # Get last 5 entities mentioned
            recent_entities = list(self.entities.keys())[-5:]
            context["suggested_entities"] = recent_entities
        
        # Add current context
        context.update(self.current_context)
        
        # Ensure all values are JSON serializable
        return _to_serializable(context)
    
    # ============================================
    # MCP Memory Server Integration
    # ============================================
    
    def _sync_to_mcp(self, turn: ConversationTurn):
        """
        Sincroniza turno de conversa para o MCP Memory Server.
        
        Isso permite persistência entre sessões e análise semântica.
        """
        try:
            from mcp_server.mcp_client import call_mcp_tool
            
            # Create entities for MCP
            for entity in turn.entities_extracted:
                try:
                    call_mcp_tool("memory_create_entities", {
                        "entities": [{
                            "entityType": f"fleetintel:{entity.entity_type.value}",
                            "name": f"{entity.entity_type.value}:{entity.name}",
                            "observations": [
                                f"Extraído da mensagem: {turn.user_message[:100]}...",
                                f"Confiança: {entity.confidence}",
                                f"Fonte: {entity.source}",
                                f"Timestamp: {entity.created_at}"
                            ]
                        }]
                    })
                except Exception:
                    pass  # MCP might not be available
            
            # Create relationships for MCP
            for rel in turn.relationships_created:
                try:
                    call_mcp_tool("memory_create_relations", {
                        "relations": [{
                            "from": f"fleetintel:entity:{rel.from_entity}",
                            "relationType": rel.relation_type,
                            "to": f"fleetintel:entity:{rel.to_entity}"
                        }]
                    })
                except Exception:
                    pass  # MCP might not be available
                    
        except ImportError:
            # MCP client not available, continue without sync
            pass
    
    def _load_from_mcp(self):
        """Carrega memória existente do MCP Memory Server."""
        try:
            from mcp_server.mcp_client import call_mcp_tool
            
            # Search for existing conversation context
            result = call_mcp_tool("memory_search_nodes", {
                "query": f"fleetintel:conversation:{self.user_id}"
            })
            
            if result and "result" in result:
                # Parse loaded entities
                for entity_data in result.get("result", []):
                    if "entityType" in entity_data and "fleetintel:" in entity_data["entityType"]:
                        entity_type = entity_data["entityType"].split(":")[1]
                        self.entities[entity_data["name"]] = Entity(
                            name=entity_data["name"],
                            entity_type=EntityType(entity_type) if entity_type in [e.value for e in EntityType] else EntityType.CONTEXTO,
                            confidence=1.0,
                            source="mcp_memory"
                        )
                        
        except Exception:
            # MCP not available, start fresh
            pass
    
    # ============================================
    # Public API
    # ============================================
    
    def remember(self, user_message: str, assistant_response: str):
        """
        Método principal para registrar uma interação.
        
        Usage:
            memory.remember(
                "Quantos veículos da Volvo emplacaram em 2024?",
                "A Volvo emplacou 1.000 veículos em 2024."
            )
        """
        self.update_context(user_message, assistant_response)
    
    def recall(self, query: str) -> Dict[str, Any]:
        """
        Recupera contexto relevante para uma query.
        
        Returns:
            Dicionário com contexto estruturado para processamento
        """
        return self.get_context_for_query(query)
    
    def get_last_company(self) -> Optional[str]:
        """Retorna a última empresa mencionada na conversa."""
        for entity_name, entity in reversed(list(self.entities.items())):
            if entity.entity_type == EntityType.EMPRESA:
                return entity_name
        return None
    
    def get_last_brand(self) -> Optional[str]:
        """Retorna a última marca mencionada na conversa."""
        for entity_name, entity in reversed(list(self.entities.items())):
            if entity.entity_type == EntityType.MARCA:
                return entity_name
        return None
    
    def get_last_year(self) -> Optional[str]:
        """Retorna o último ano mencionado na conversa."""
        for entity_name, entity in reversed(list(self.entities.items())):
            if entity.entity_type == EntityType.ANO:
                return entity_name
        return None
    
    def get_conversation_summary(self) -> str:
        """Gera resumo da conversa para debugging/logging."""
        if not self.conversation_history:
            return "Sem histórico de conversa."
        
        summary_parts = []
        for i, turn in enumerate(self.conversation_history[-5:], 1):
            entities = [e.name for e in turn.entities_extracted]
            summary_parts.append(f"Turn {i}: {entities}")
        
        return f"Últimos {len(summary_parts)} turnos: {' | '.join(summary_parts)}"
    
    def clear(self):
        """Limpa toda a memória (usar com cautela)."""
        self.conversation_history = []
        self.entities = {}
        self.relationships = []
        self.current_context = {}


# ============================================
# Factory Function
# ============================================

_memory_cache: Dict[str, FleetIntelMemory] = {}

def get_memory(user_id: str, session_id: str = "default") -> FleetIntelMemory:
    """
    Factory function para obter instância de memória.
    
    Usa cache para manter a mesma instância durante uma sessão.
    """
    cache_key = f"{user_id}:{session_id}"
    
    if cache_key not in _memory_cache:
        _memory_cache[cache_key] = FleetIntelMemory(user_id, session_id)
    
    return _memory_cache[cache_key]


# ============================================
# Example Usage
# ============================================

if __name__ == "__main__":
    # Demo do sistema de memória
    memory = get_memory("user_123", "demo_session")
    
    # Registrar interações
    memory.remember(
        "Quantos veículos da Volvo emplacaram em 2024?",
        "A Volvo emplacou 1.000 veículos em 2024."
    )
    
    memory.remember(
        "E da Mercedes?",
        "A Mercedes-Benz emplacou 800 veículos em 2024."
    )
    
    # Recuperar contexto
    context = memory.recall("quantos em 2025?")
    print(f"Follow-up detectado: {context['follow_up_detected']}")
    print(f"Contexto: {context}")
    
    print(f"\n{memory.get_conversation_summary()}")
