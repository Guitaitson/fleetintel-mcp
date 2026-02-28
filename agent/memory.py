"""FleetIntel Agent Memory System v4 - State of the Art Wrapper

Sistema de memória que encapsula o FleetIntelMemory (Knowledge Graph)
mantendo a API original para backward compatibility.

Usage:
    from agent.memory import AgentMemory
    
    memory = AgentMemory(user_id="user_123")
    memory.add_message("user", "quantos veículos tem no banco?")
    context = memory.get_context()
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Import the new state-of-the-art memory system
from agent.memory_state_of_the_art import (
    FleetIntelMemory,
    get_memory as get_fleet_memory,
)


class AgentMemory:
    """
    Sistema de memória persistente para o agente v4.
    
    Internamente usa FleetIntelMemory (Knowledge Graph) para
    armazenamento de estado da arte, mantendo API original.
    """
    
    def __init__(self, user_id: str, session_id: str = "default"):
        """
        Inicializa o sistema de memória.
        
        Args:
            user_id: Identificador único do usuário
            session_id: ID da sessão (para múltiplas conversas)
        """
        self.user_id = user_id
        self.session_id = session_id
        
        # Internal state-of-the-art memory
        self._fleet_memory: Optional[FleetIntelMemory] = None
        
        # Legacy data structures (for backward compatibility)
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.learned_facts: List[str] = []
        self.query_patterns: Dict[str, int] = {}
        
        # Initialize fleet memory
        self._init_fleet_memory()
    
    def _init_fleet_memory(self):
        """Inicializa a memória de estado da arte."""
        try:
            self._fleet_memory = get_fleet_memory(self.user_id, self.session_id)
        except Exception:
            # Fallback to legacy if fleet memory fails
            self._fleet_memory = None
    
    def _ensure_dir(self):
        """Garante que o diretório de memória existe."""
        Path(".agent_memory").mkdir(parents=True, exist_ok=True)
    
    def _save_legacy(self):
        """Salva dados legados para backup."""
        self._ensure_dir()
        memory_file = Path(".agent_memory") / f"{self.user_id}_legacy.json"
        data = {
            'conversation_history': self.conversation_history,
            'user_preferences': self.user_preferences,
            'learned_facts': self.learned_facts,
            'query_patterns': self.query_patterns,
            'updated_at': datetime.utcnow().isoformat()
        }
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Adiciona mensagem ao histórico.
        
        Args:
            role: 'user', 'assistant', ou 'tool'
            content: Texto da mensagem
            metadata: Informações adicionais (opcional)
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            message['metadata'] = metadata
        
        self.conversation_history.append(message)
        
        # Update fleet memory if available
        if self._fleet_memory and role in ['user', 'assistant']:
            # Find the pair and add to fleet memory
            if role == 'user':
                self._last_user_message = content
            elif role == 'assistant' and hasattr(self, '_last_user_message'):
                self._fleet_memory.remember(self._last_user_message, content)
                del self._last_user_message
        
        # Limit history
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        self._save_legacy()
    
    def add_conversation_turn(self, user_message: str, assistant_message: str,
                               tools_used: Optional[List[str]] = None):
        """
        Adiciona um turno completo de conversa.
        
        Args:
            user_message: Mensagem do usuário
            assistant_message: Resposta do assistente
            tools_used: Lista de ferramentas utilizadas
        """
        self.add_message('user', user_message, {'tools_used': tools_used})
        self.add_message('assistant', assistant_message)
    
    def remember_fact(self, fact: str, category: str = 'general'):
        """
        Aprende um fato sobre o usuário ou preferências.
        
        Args:
            fact: Fato a ser lembrado
            category: Categoria do fato ('preference', 'interest', 'behavior', 'general')
        """
        fact_entry = {
            'fact': fact,
            'category': category,
            'learned_at': datetime.utcnow().isoformat()
        }
        
        # Avoid duplicates
        existing = [f for f in self.learned_facts if isinstance(f, dict) and f.get('fact') == fact]
        if not existing:
            if isinstance(self.learned_facts) and len(self.learned_facts) > 0 and isinstance(self.learned_facts[0], str):
                # Convert to new format
                self.learned_facts = [f for f in self.learned_facts if isinstance(f, dict)]
            
            self.learned_facts.append(fact_entry)
            self._save_legacy()
    
    def learn_preference(self, key: str, value: Any):
        """
        Aprende uma preferência do usuário.
        
        Args:
            key: Chave da preferência
            value: Valor da preferência
        """
        self.user_preferences[key] = {
            'value': value,
            'set_at': datetime.utcnow().isoformat()
        }
        self._save_legacy()
    
    def record_query_pattern(self, query_type: str):
        """
        Registra um padrão de consulta para análise.
        
        Args:
            query_type: Tipo de consulta (ex: 'count_vehicles', 'ranking_empresas')
        """
        self.query_patterns[query_type] = self.query_patterns.get(query_type, 0) + 1
        self._save_legacy()
    
    def get_context(self, include_history: bool = True, max_history: int = 5) -> str:
        """
        Retorna contexto formatado para o prompt.
        
        Args:
            include_history: Se deve incluir histórico de conversas
            max_history: Número máximo de mensagens do histórico
            
        Returns:
            String formatada com contexto
        """
        context_parts = []
        
        # Get context from fleet memory (state-of-the-art)
        if self._fleet_memory:
            fleet_context = self._fleet_memory.recall("")
            if fleet_context.get('follow_up_detected'):
                context_parts.append(f"🔗 Contexto: {fleet_context.get('referenced_entities', [])}")
        
        # Conhecimentos aprendidos (legacy)
        if self.learned_facts:
            facts = [f['fact'] if isinstance(f, dict) else f for f in self.learned_facts[-10:]]
            context_parts.append(f"📚 Conhecimentos prévios: {'; '.join(facts)}")
        
        # Preferências (legacy)
        if self.user_preferences:
            prefs = [f"{k}: {v['value']}" for k, v in list(self.user_preferences.items())[-5:]]
            context_parts.append(f"⚙️ Preferências: {', '.join(prefs)}")
        
        # Histórico de conversas (legacy)
        if include_history and self.conversation_history:
            recent_msgs = self.conversation_history[-max_history:]
            history_lines = []
            for msg in recent_msgs:
                role = msg['role'].upper()
                content = msg['content'][:100] if len(msg['content']) > 100 else msg['content']
                history_lines.append(f"[{role}]: {content}")
            context_parts.append(f"💬 Histórico recente:\n" + "\n".join(history_lines))
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da conversa atual.
        
        Returns:
            Dicionário com resumo
        """
        user_msgs = [m for m in self.conversation_history if m['role'] == 'user']
        assistant_msgs = [m for m in self.conversation_history if m['role'] == 'assistant']
        
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len(user_msgs),
            'assistant_messages': len(assistant_msgs),
            'facts_learned': len(self.learned_facts),
            'preferences_set': len(self.user_preferences),
            'top_query_types': dict(sorted(self.query_patterns.items(), 
                                          key=lambda x: x[1], reverse=True)[:5]),
            'fleet_memory_active': self._fleet_memory is not None
        }
    
    def clear_history(self, keep_facts: bool = True):
        """
        Limpa histórico de conversas.
        
        Args:
            keep_facts: Se deve manter fatos aprendidos
        """
        if keep_facts:
            facts = self.learned_facts
            prefs = self.user_preferences
        else:
            facts = []
            prefs = {}
        
        self.conversation_history = []
        self.learned_facts = facts
        self.user_preferences = prefs
        self._save_legacy()
    
    def export_memory(self) -> Dict[str, Any]:
        """Exporta toda a memória como dicionário."""
        return {
            'user_id': self.user_id,
            'conversation_history': self.conversation_history,
            'user_preferences': self.user_preferences,
            'learned_facts': self.learned_facts,
            'query_patterns': self.query_patterns,
            'exported_at': datetime.utcnow().isoformat()
        }
    
    def import_memory(self, data: Dict[str, Any]):
        """Importa memória de dicionário."""
        self.conversation_history = data.get('conversation_history', [])
        self.user_preferences = data.get('user_preferences', {})
        self.learned_facts = data.get('learned_facts', [])
        self.query_patterns = data.get('query_patterns', {})
        self._save_legacy()


# Funções de conveniência
def get_memory(user_id: str) -> AgentMemory:
    """Obtém instância de memória para um usuário."""
    return AgentMemory(user_id)


def get_user_context(user_id: str) -> str:
    """Obtém contexto formatado para um usuário."""
    memory = AgentMemory(user_id)
    return memory.get_context()
