# Arquitetura MCP - Redesenho para Performance

## Problema Atual

O agente atual tem dois problemas críticos:

### 1. Recursão no LangGraph
```
Erro: Recursion limit of 25 reached without hitting a stop condition
```

Causa: `create_react_agent` permite que o agent execute múltiplas tool calls em loop, especialmente quando:
- O LLM decide chamar várias ferramentas sequencialmente
- As ferramentas retornam dados que geram mais perguntas do agent
- Não há "stop condition" clara

### 2. Sobrecarga de SQL Direto
Cada mensagem do usuário gera queries SQL diretas:
- Queries não otimizadas
- Sem cache
- Sem controle de rate limiting
- Banco de dados sobrecarregado

## Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                      TELEGRAM BOT                               │
│                    (app/integrations/)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGRAPH AGENT                                │
│  - Interpreta intenção do usuário                               │
│  - Decide quais ferramentas chamar                              │
│  - Formata resposta final                                       │
│  - USA MCP TOOLS como ferramentas                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVER + CLIENT                           │
│  - Ferramentas pré-definidas                                   │
│  - Cache Redis/DB                                               │
│  - Queries otimizadas                                           │
│  - Rate limiting                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   POSTGRESQL / SUPABASE                          │
│  - Dados normalizados                                           │
│  - Índices otimizados                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Solução: MCP Tools como Interface

### Step 1: Criar MCP Tools Otimizadas

Em `mcp_server/mcp_tools.py`:

```python
from mcp_server.main import app, call_tool

# Ferramentas com cache e otimização

async def top_empresas_por_emplacamento(ano: int, uf: str = None, top_n: int = 10) -> dict:
    """TOP N empresas por emplacamento - com cache 1h."""
    
    # Verificar cache primeiro
    cache_key = f"top_emplacamentos:{ano}:{uf}:{top_n}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query otimizada
    query = """
        SELECT e.id, e.razao_social, e.nome_fantasia, 
               COUNT(r.id) as total, SUM(r.preco) as valor_total
        FROM empresas e
        JOIN registrations r ON e.id = r.empresa_id
        WHERE EXTRACT(YEAR FROM r.data_emplacamento) = :ano
        {uf_filter}
        GROUP BY e.id, e.razao_social, e.nome_fantasia
        ORDER BY total DESC
        LIMIT :top_n
    """
    
    # Executar e cachear
    result = await db.execute(query, params)
    
    await redis.setex(cache_key, 3600, json.dumps(result))  # 1 hora
    
    return result
```

### Step 2: Agent Usa MCP em vez de SQL

Em `agent/agent.py`:

```python
# NÃO FAREMOS MAIS ISSO:
# @tool
# async def top_empresas_by_registrations(ano: int, ...):
#     query = text("SELECT ...")
#     return await session.execute(query)

# EM VEZ DISSO:
from mcp_server.client import MCPClient

mcp_client = MCPClient()

@tool
async def top_empresas_by_emplacamento(ano: int, uf: str = None, top_n: int = 10) -> dict:
    """TOP N empresas por emplacamento usando MCP."""
    result = await mcp_client.call_tool(
        "top_empresas_por_emplacamento",
        {"ano": ano, "uf": uf, "top_n": top_n}
    )
    return result
```

### Step 3: Configurar Recursion Limit

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint import MemorySaver

# Configurar checkpoint e limits
config = RunnableConfig(
    recursion_limit=10,  # Reduzir de 25 para 10
    max_iterations=5,
)

agent = create_react_agent(model, tools, config=config)
```

## Ferramentas MCP Prioritárias

| Ferramenta | Cache | Descrição |
|------------|-------|-----------|
| `top_empresas_por_emplacamento` | 1h | TOP 10 empresas por ano/UF |
| `contagem_veiculos_marca` | 1h | Contagem por marca |
| `registrations_por_periodo` | 30min | Registros por data |
| `estatisticas_gerais` | 5min | Stats do banco |
| `busca_veiculo_placa` | 1h | Busca por placa |

## Implementação em Fases

### Fase 1: Correção de Recursão (RÁPIDO)
- [ ] Reduzir `recursion_limit` de 25 para 10
- [ ] Adicionar `max_iterations` no agent
- [ ] Testar com consultas simples

### Fase 2: MCP Tools Básicas (MÉDIO)
- [ ] Criar `mcp_client.py` para conectar ao MCP Server
- [ ] Mover `top_empresas_by_registrations` para MCP
- [ ] Adicionar cache Redis às queries

### Fase 3: Cache Completo (LONGO)
- [ ] Adicionar Redis ao projeto
- [ ] Implementar cache em todas as ferramentas
- [ ] Adicionar rate limiting

## Scripts de Validação

```python
# test_mcp_integration.py
async def test_agent_without_recursion():
    """Testa que o agent não entra em recursão."""
    
    # Configurar agent com limites
    agent = create_react_agent(
        model, 
        tools,
        config={"recursion_limit": 10}
    )
    
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="Qual empresa mais emplacou em 2025?")]
    })
    
    # Deve retornar resposta em no máximo 2 tool calls
    assert len(result.get("tool_calls", [])) <= 2
```

## Conclusão

O redesign vai:
1. ✅ Eliminar recursão → agent para após 2-3 tool calls
2. ✅ Melhorar performance → cache reduz queries ao DB
3. ✅ Reduzir carga DB → queries pré-otimizadas
4. ✅ Separar responsabilidades → SQL isolado em MCP
