"""FleetIntel Intelligent Response Generator

Gerador de respostas inteligentes para o agente LangGraph.
Formata dados do banco em respostas conversacionais e proativas.

Usage:
    from agent.responses import IntelligentResponseGenerator
    
    generator = IntelligentResponseGenerator()
    response = generator.format_response(query_type, tool_results, context)
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class IntelligentResponseGenerator:
    """Gerador de respostas inteligentes."""
    
    # Constantes para formatação
    TOTAL_VEHICLES = 986859
    TOTAL_REGISTRATIONS = 919941
    TOTAL_EMPRESAS = 161932
    
    def __init__(self):
        self.entity_mapping = {
            "search_vehicles": "veículo",
            "search_empresas": "empresa",
            "search_registrations": "emplacamento",
            "top_empresas_by_registrations": "empresa",
            "get_stats": "estatística",
        }
    
    def format_response(self, query_type: str, results: Dict[str, Any], 
                       query: str, context: Optional[str] = None) -> str:
        """
        Formata resposta baseada no tipo de consulta.
        
        Args:
            query_type: Tipo de consulta (search_vehicles, ranking, etc.)
            results: Resultados da ferramenta MCP
            query: Query original do usuário
            context: Contexto adicional (memória)
            
        Returns:
            Resposta formatada em texto
        """
        # Classificar tipo de resposta
        if query_type == "get_stats":
            return self._format_stats_response(results)
        elif "count" in results and "query" in results:
            return self._format_count_response(results, query)
        elif "vehicles" in results:
            return self._format_vehicles_response(results.get("vehicles", []), query)
        elif "empresas" in results:
            return self._format_empresas_response(results.get("empresas", []), query)
        elif "registrations" in results:
            return self._format_registrations_response(results.get("registrations", []), query)
        else:
            return self._format_general_response(results, query)
    
    def _format_count_response(self, results: Dict[str, Any], query: str) -> str:
        """Formata resposta para perguntas de contagem."""
        count = results.get("count", 0)
        query_type = results.get("query", "")
        
        if count == 0:
            return "🔍 Nenhum resultado encontrado para essa consulta.\n\nTente reformular a pergunta ou usar filtros diferentes."
        
        entity = self.entity_mapping.get(query_type, "resultado")
        plural_entity = entity if count != 1 else entity
        
        # Extrair contexto da query
        context = self._extract_query_context(query)
        
        response = f"📊 **Resultado da Consulta**\n\n"
        response += f"Encontrei **{count:,} {plural_entity}" + ("s" if count != 1 else "") + "**"
        
        if context:
            response += f" {context}"
        else:
            response += " no banco de dados"
        
        response += ".\n"
        
        # Adicionar insight contextual
        insight = self._generate_count_insight(count, query_type)
        if insight:
            response += f"\n💡 {insight}"
        
        return response
    
    def _format_vehicles_response(self, vehicles: List[Dict], query: str) -> str:
        """Formata resposta para lista de veículos."""
        if not vehicles:
            return "🔍 Nenhum veículo encontrado para os critérios informados."
        
        count = len(vehicles)
        
        # Header
        response = f"🚗 **Veículos Encontrados: {count}**\n\n"
        
        # Preview dos primeiros veículos
        for i, v in enumerate(vehicles[:5], 1):
            marca = v.get('marca_nome') or v.get('marca', 'N/A')
            modelo = v.get('modelo_nome') or v.get('modelo', '')
            placa = v.get('placa', 'N/A')
            ano = v.get('ano_fabricacao', '')
            
            if modelo:
                response += f"{i}. **{marca} {modelo}**"
            else:
                response += f"{i}. **{marca}**"
            
            if ano:
                response += f" ({ano})"
            response += f" - Placa: {placa}\n"
        
        # Se há mais veículos
        if count > 5:
            response += f"\n... e mais **{count - 5} veículos**"
        
        # Adicionar filtros mencionados
        filters = self._extract_filters_from_query(query)
        if filters:
            response += f"\n\n🔍 Filtros aplicados: {filters}"
        
        return response
    
    def _format_empresas_response(self, empresas: List[Dict], query: str) -> str:
        """Formata resposta para lista de empresas."""
        if not empresas:
            return "🔍 Nenhuma empresa encontrada para os critérios informados."
        
        count = len(empresas)
        
        # Verificar se é um ranking
        is_ranking = any('total_registrations' in e for e in empresas)
        
        if is_ranking:
            response = f"🏆 **Ranking de Empresas ({count})**\n\n"
            for i, e in enumerate(empresas[:10], 1):
                nome = e.get('nome_fantasia') or e.get('razao_social', 'N/A')
                segmento = e.get('segmento_cliente', e.get('segmento', ''))
                total = e.get('total_registrations', 0)
                valor = e.get('total_valor', 0)
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                response += f"{medal} **{nome}**"
                if segmento:
                    response += f" ({segmento})"
                response += f"\n   └─ {total:,} emplacamentos"
                if valor:
                    response += f" | R$ {valor:,.0f}"
                response += "\n"
            
            if count > 10:
                response += f"\n... e mais **{count - 10} empresas**"
        else:
            response = f"🏢 **Empresas Encontradas: {count}**\n\n"
            for i, e in enumerate(empresas[:10], 1):
                nome = e.get('nome_fantasia') or e.get('razao_social', 'N/A')
                cnpj = e.get('cnpj', 'N/A')
                segmento = e.get('segmento_cliente', e.get('segmento', ''))
                
                response += f"{i}. **{nome}**"
                if segmento:
                    response += f" ({segmento})"
                response += f"\n   └─ CNPJ: {cnpj}\n"
            
            if count > 10:
                response += f"\n... e mais **{count - 10} empresas**"
        
        return response
    
    def _format_registrations_response(self, registrations: List[Dict], query: str) -> str:
        """Formata resposta para lista de emplacamentos."""
        if not registrations:
            return "🔍 Nenhum emplacamento encontrado para os critérios informados."
        
        count = len(registrations)
        
        response = f"📋 **Emplacamentos Encontrados: {count}**\n\n"
        
        # Calcular totais
        total_value = sum(r.get('preco', 0) for r in registrations)
        
        for i, r in enumerate(registrations[:5], 1):
            marca = r.get('marca_nome') or r.get('marca', 'N/A')
            modelo = r.get('modelo_nome') or r.get('modelo', '')
            placa = r.get('placa', 'N/A')
            data = r.get('data_emplacamento', 'N/A')
            preco = r.get('preco', 0)
            empresa = r.get('razao_social', '')
            
            response += f"{i}. **{marca} {modelo}** - {placa}\n"
            response += f"   📅 {data} | "
            response += f"💰 R$ {preco:,.0f}" if preco else "💰 Preço não disponível"
            if empresa:
                response += f" | 🏢 {empresa}"
            response += "\n"
        
        if count > 5:
            response += f"\n... e mais **{count - 5} emplacamentos**"
        
        if total_value > 0:
            response += f"\n\n💵 **Total: R$ {total_value:,.0f}**"
        
        return response
    
    def _format_stats_response(self, stats: Dict[str, Any]) -> str:
        """Formata estatísticas do banco."""
        response = "📊 **Estatísticas do Banco de Dados**\n\n"
        
        # Estatísticas principais
        main_stats = {
            'vehicles': ('🚗', 'Veículos'),
            'empresas': ('🏢', 'Empresas'),
            'registrations': ('📋', 'Emplacamentos'),
            'marcas': ('🏭', 'Marcas'),
            'modelos': ('📦', 'Modelos'),
        }
        
        for key, (icon, label) in main_stats.items():
            value = stats.get(key, 0)
            if isinstance(value, (int, float)):
                response += f"{icon} **{label}:** {value:,}\n"
            else:
                response += f"{icon} **{label}:** {value}\n"
        
        # Calcular insights
        vehicles = stats.get('vehicles', 0)
        registrations = stats.get('registrations', 0)
        
        if vehicles > 0:
            coverage = (registrations / vehicles) * 100
            response += f"\n📈 **Cobertura de emplacamentos:** {coverage:.1f}%"
        
        return response
    
    def _format_general_response(self, results: Dict[str, Any], query: str) -> str:
        """Formata resposta genérica para resultados não categorizados."""
        response = "📊 **Resultado**\n\n"
        
        # Tentar extrair informação relevante
        if isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, (int, float)) and key != 'timestamp':
                    response += f"- **{key.title()}:** {value:,}\n"
                elif isinstance(value, list) and len(value) > 0:
                    response += f"- **{key.title()}:** {len(value)} itens encontrados\n"
        else:
            response += str(results)
        
        return response
    
    def _extract_query_context(self, query: str) -> str:
        """Extrai contexto adicional da query."""
        query_lower = query.lower()
        
        contexts = []
        
        if "2024" in query:
            contexts.append("em 2024")
        elif "2025" in query:
            contexts.append("em 2025")
        elif "2026" in query:
            contexts.append("em 2026")
        
        if "caminhão" in query_lower or "caminhao" in query_lower:
            contexts.append("de caminhões")
        elif "ônibus" in query_lower or "onibus" in query_lower:
            contexts.append("de ônibus")
        elif "van" in query_lower:
            contexts.append("de vans")
        elif "carro" in query_lower or "automóvel" in query_lower:
            contexts.append("de automóveis")
        
        if "sp" in query.lower():
            contexts.append("em São Paulo")
        elif "mg" in query.lower():
            contexts.append("em Minas Gerais")
        elif "rj" in query.lower():
            contexts.append("no Rio de Janeiro")
        elif "pr" in query.lower():
            contexts.append("no Paraná")
        
        return " ".join(contexts) if contexts else ""
    
    def _extract_filters_from_query(self, query: str) -> str:
        """Extrai filtros mencionados na query."""
        query_lower = query.lower()
        filters = []
        
        if "fiat" in query_lower:
            filters.append("Fiat")
        if "volkswagen" in query_lower or "vw" in query_lower:
            filters.append("Volkswagen")
        if "mercedes" in query_lower:
            filters.append("Mercedes-Benz")
        if "volvo" in query_lower:
            filters.append("Volvo")
        if "scan" in query_lower:
            filters.append("Scania")
        
        if "locadora" in query_lower:
            filters.append("segmento: Locadora")
        if "frota" in query_lower:
            filters.append("frota comercial")
        
        return ", ".join(filters) if filters else ""
    
    def _generate_count_insight(self, count: int, query_type: str) -> str:
        """Gera insight contextual baseado na contagem."""
        if count == 0:
            return "Tente ampliar os filtros ou fazer uma busca mais geral."
        
        if query_type == "search_vehicles":
            pct = (count / self.TOTAL_VEHICLES) * 100
            if pct < 1:
                return f"Representa menos de 1% do total de veículos no banco."
            elif pct < 10:
                return f"Representa {pct:.1f}% do total de veículos."
            else:
                return "Volume significativo de veículos!"
        
        elif query_type == "search_empresas":
            pct = (count / self.TOTAL_EMPRESAS) * 100
            if pct < 1:
                return "Grupo seleto de empresas."
            else:
                return f"Parceria com {pct:.1f}% das empresas cadastradas."
        
        elif query_type == "search_registrations":
            pct = (count / self.TOTAL_REGISTRATIONS) * 100
            if pct < 1:
                return "Período ou região com volume baixo de emplacamentos."
            else:
                return f"Período/régião representativo ({pct:.1f}% dos emplacamentos)."
        
        return ""


class ProactiveSuggestionEngine:
    """Motor de sugestões proativas."""
    
    # Templates de sugestões por tipo de resposta
    SUGGESTION_TEMPLATES = {
        "count_low": [
            "Quer filtrar por estado ou marca para encontrar mais opções?",
            "Posso analisar por período, se preferir.",
            "Quer ver o ranking das principais empresas nesse segmento?",
        ],
        "count_high": [
            "Esse número é bem interessante! Quer ver o ranking por estado?",
            "Quer analisar quais marcas mais contribuíram para esse total?",
            "Posso gerar um relatório detalhado por período.",
        ],
        "ranking_top": [
            "A líder do mercado! Quer ver a evolução dela nos últimos anos?",
            "Interessante! Quer saber o que fez eles liderarem?",
            "Quer comparar com a segunda colocada?",
        ],
        "vehicles_found": [
            "Quer ver mais detalhes de algum veículo específico?",
            "Posso buscar veículos similares ou de marcas relacionadas.",
            "Quer salvar essa busca para referência futura?",
        ],
        "empresas_found": [
            "Quer ver o histórico de emplacamentos de alguma empresa?",
            "Posso comparar empresas do mesmo segmento.",
            "Quer filtrar por região ou porte?",
        ],
        "registrations_found": [
            "Quer ver a evolução mensal desse padrão?",
            "Posso analisar por marca ou modelo.",
            "Quer exportar esses dados para análise?",
        ],
    }
    
    def get_suggestion(self, response_type: str, data: Dict[str, Any]) -> str:
        """
        Gera sugestão proativa baseada nos dados.
        
        Args:
            response_type: Tipo de resposta
            data: Dados da resposta
            
        Returns:
            Sugestão formatada
        """
        import random
        
        templates = self.SUGGESTION_TEMPLATES.get(response_type, 
                                                   self.SUGGESTION_TEMPLATES.get("count_low", []))
        
        if not templates:
            return ""
        
        suggestion = random.choice(templates)
        
        # Preencher placeholders se houver
        if "{empresa}" in suggestion and "nome_fantasia" in data:
            suggestion = suggestion.replace("{empresa}", data["nome_fantasia"])
        elif "{count}" in suggestion:
            count = data.get("count", 0)
            suggestion = suggestion.replace("{count}", f"{count:,}")
        
        return f"\n\n🤔 {suggestion}"
    
    def generate_followup_questions(self, query: str, results: Dict[str, Any]) -> List[str]:
        """
        Gera perguntas de follow-up baseadas na query e resultados.
        
        Args:
            query: Query original
            results: Resultados
            
        Returns:
            Lista de perguntas sugeridas
        """
        questions = []
        query_lower = query.lower()
        
        if "emplacou" in query_lower or "comprou" in query_lower:
            questions.append("Qual foi a marca mais comprada?")
            questions.append("Em quais estados foram os emplacamentos?")
        elif "quantos" in query_lower or "quantas" in query_lower:
            questions.append("E por marca?")
            questions.append("Qual a distribuição por estado?")
        elif "ranking" in query_lower or "maior" in query_lower:
            questions.append("E a segunda colocada?")
            questions.append("Qual o crescimento comparado ao ano anterior?")
        
        return questions[:2]  # Máximo 2 sugestões
