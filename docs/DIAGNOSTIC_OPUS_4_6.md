# FleetIntel — Diagnóstico Completo e Correções

**Data:** 2026-02-08  
**Analista:** Claude Opus 4.6  
**Método:** Análise estática de todo o codebase local

---

## 🔴 Resumo Executivo

Encontrei **7 bugs**, sendo **3 críticos** que explicam 100% do problema "Sem dados".  
O ROLLBACK no log **NÃO é um bug** — é comportamento normal do SQLAlchemy.

| # | Severidade | Arquivo | Problema |
|---|-----------|---------|----------|
| 1 | 🔴 CRÍTICO | `agent/agent.py` | Chave errada: verifica `'empresas'` mas a função retorna `'results'` |
| 2 | 🔴 CRÍTICO | `agent/agent.py` | `call_mcp_tool()` recebe dict posicional em vez de **kwargs |
| 3 | 🔴 CRÍTICO | `agent/agent.py` | Passa `empresa_id` mas MCPClient espera `razao_social` |
| 4 | 🟡 MÉDIO | `mcp_server/vector_search.py` | Embedding passado como string sem cast para `::vector` |
| 5 | 🟡 MÉDIO | `agent/memory_state_of_the_art.py` | `_sync_to_mcp` chama função async sem `await` |
| 6 | 🟡 MÉDIO | `agent/memory_state_of_the_art.py` | Tools `memory_create_entities` não existem no MCPClient |
| 7 | 🟢 INFO | Log ROLLBACK | É comportamento normal do SQLAlchemy para SELECT queries |

---

Documento completo: ver FLEETINTEL_DIAGNOSTIC.md
