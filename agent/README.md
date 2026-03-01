# FleetIntel LangGraph Agent

Agente conversacional para processar consultas complexas sobre dados de frota usando LangGraph para orquestracao e as MCP tools como ferramentas.

## Descricao

Este modulo implementa um agente de IA que:
- Interpreta perguntas em linguagem natural
- Orquestra multiplas consultas ao banco de dados
- Agrega e sumariza resultados
- Gera insights via LLM

## Arquitetura

```
                    +------------------+
                    |   Human Message  |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  analyze_query   |  <- Analisa tipo de consulta
                    +--------+---------+
                             |
                    +--------v---------+
                    |  execute_query   |  <- Executa buscas
                    +--------+---------+
                             |
                    +--------v---------+
                    | generate_response|  <- Gera resposta
                    +--------+---------+
                             |
                    +--------v---------+
                    |       END        |
                    +------------------+
```

## Ferramentas Disponiveis

| Funcao | Descricao |
|--------|-----------|
| `get_stats()` | Estatisticas do banco |
| `search_vehicles()` | Busca veiculos com filtros |
| `search_vehicles_count()` | Conta veiculos (otimizado) |
| `search_empresas()` | Busca empresas |
| `search_registrations()` | Busca registros |
| `search_registrations_count()` | Conta registros (otimizado) |

## Instalacao

```bash
# Instalar dependencias
uv pip install langgraph langchain-openai

# Configurar variaveis de ambiente
export OPENAI_API_KEY="sua-api-key"
```

## Uso Basico

```python
import asyncio
from agent.agent import run_query

async def main():
    # Consulta simples
    result = await run_query("Quantos veiculos estao cadastrados?")
    print(result)
    
    # Consulta com filtros
    result = await run_query("Quantos veiculos da FIAT foram emplacados em SP em 2024?")
    print(result)

asyncio.run(main())
```

## Uso Avancado

```python
from agent.agent import create_agent, AgentState
from langchain_core.messages import HumanMessage

# Criar grafo
graph = create_agent()
app = graph.compile()

# Estado inicial
state = AgentState(
    messages=[HumanMessage(content="Sua pergunta aqui")],
    current_query="Sua pergunta aqui",
)

# Executar
result = await app.ainvoke(state)
print(result.final_answer)
```

## Exemplos de Consultas

| Pergunta | Tipo |
|----------|------|
| "Quantos veiculos estao cadastrados?" | VEHICLE_COUNT |
| "Quantos veiculos da FIAT foram emplacados em 2024?" | REGISTRATION_COUNT |
| "Liste as empresas do segmento LOCADORA" | EMPRESA_LIST |
| "Quais sao as estatisticas do banco?" | STATS |
| "Compare o numero de emplacamentos entre SP e RJ" | COMPARISON |

## Estrutura do Projeto

```
agent/
├── __init__.py        # Exports principais
├── agent.py          # Implementacao do agente
├── test_agent.py     # Testes
└── README.md         # Esta documentacao
```

## Integracao com MCP

O agente pode usar as tools do MCP server diretamente ou as funcoes locais em `agent/agent.py`. As tools locais dao mais controle e funcionam sem necessidade de servidor MCP rodando.

## Requisitos

- Python 3.11+
- LangGraph >=0.2.70
- LangChain >=0.3.14
- OpenAI API Key

## Licenca

MIT
