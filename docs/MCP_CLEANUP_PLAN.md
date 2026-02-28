# Plano de Limpeza e Integração MCP

## Situação Atual (Duplicação)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP SERVER (EXISTE)                          │
│                    mcp_server/main.py                                │
│                                                                     │
│  Tools disponíveis:                                                 │
│  - search_vehicles      ✅                                          │
│  - search_empresas      ✅                                          │
│  - search_registrations ✅                                          │
│  - get_stats           ✅                                          │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    │ NÃO USADO PELO AGENT!
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH AGENT (DUPLICADO)                      │
│                    agent/agent.py                                    │
│                                                                     │
│  Tools PRÓPRIAS (DEVEM SER REMOVIDAS):                              │
│  - get_stats()         ❌ DUPLICADO                                 │
│  - search_vehicles()   ❌ DUPLICADO                                 │
│  - search_empresas()   ❌ DUPLICADO                                 │
│  - search_registrations() ❌ DUPLICADO                              │
│  - top_empresas_by_registrations() ⚠️ FALTA NO MCP                  │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
                         SQL DIRETO (PROBLEMA!)
```

## O Que Fazer

### 1. LIMPAR: Remover Duplicações

**Deletar do agent/agent.py:**
```
❌ get_stats()         → já existe em MCP
❌ search_vehicles()    → já existe em MCP
❌ search_empresas()    → já existe em MCP
❌ search_registrations() → já existe em MCP
```

**Manter no agent/agent.py:**
```
✅ top_empresas_by_registrations() → NÃO existe em MCP! PRECISA SER ADICIONADO
```

### 2. INTEGRAR: Agent Usa MCP

Criar `mcp_server/mcp_client.py`:
```python
"""Client para LangGraph Agent acessar ferramentas MCP."""

async def call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """Chama ferramenta MCP via HTTP ou direct call."""
    # Se MCP Server rodando → chamada HTTP
    # Se agent rodando junto → direct call
```

### 3. EXPANDIR: Adicionar Ferramentas Faltando

**Adicionar ao MCP Server:**
```
⚠️ top_empresas_by_registrations() → FALTA! agent usa isso
```

## Arquitetura Alvo

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   MCP CLIENT │────▶│    AGENT     │────▶│   MCP TOOLS  │
│  (HTTP/SSE)  │     │   (limpo)    │     │  (unificadas)│
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            │                     ▼
                            │              ┌──────────────┐
                            └────────────▶│   DATABASE   │
                                           │  (uma fonte) │
                                           └──────────────┘
```

## Plano de Ação

### Fase 1: LIMPEZA (Rápido)
- [ ] Remover tools duplicadas do `agent/agent.py`
- [ ] Manter apenas `top_empresas_by_registrations()` no agent

### Fase 2: EXPANSÃO MCP (Médio)
- [ ] Adicionar `top_empresas_by_registrations()` ao `mcp_server/main.py`
- [ ] Adicionar cache às queries MCP

### Fase 3: INTEGRAÇÃO (Médio)
- [ ] Criar `mcp_server/mcp_client.py`
- [ ] Fazer agent usar tools MCP via client

### Fase 4: CORREÇÃO (Rápido)
- [ ] Adicionar `recursion_limit=10` ao agent

## Resultado Final

```
agent/agent.py       → ~50 linhas (só lógica do agent)
mcp_server/main.py   → ~400 linhas (todas as queries)
mcp_server/client.py → ~100 linhas (integração)
```

**Benefícios:**
- ✅ Elimina duplicação
- ✅ Agent mais leve
- ✅ Queries centralizadas
- ✅ Cache em um lugar só
- ✅ Manutenção facilitada
