# Roadmap do FleetIntel MCP

**Versão:** 1.0.0  
**Data:** 2026-02-02  
**Status:** Em andamento

---

## 📋 Visão Geral

O FleetIntel MCP é uma plataforma end-to-end de inteligência de frota composta por 12 épicos principais, cobrindo desde o setup inicial até o deploy em produção com monitoring completo.

**Período:** 12/01/2026 → 30/03/2026 (11 semanas)  
**Total de Épicos:** 12  
**Total de Tarefas:** 60+  
**Responsável:** Guilherme Taitson

---

## 🎯 Estrutura do Roadmap

O projeto está organizado em 4 fases principais:

### 🟣 FASE 0: FOUNDATION - DATA (Épicos 0-4)
**Período:** 12/01/2026 → 02/02/2026 (4 semanas)

Esta fase estabelece as fundações do projeto, incluindo setup inicial, banco de dados, carga de dados e integração com API externa.

| Epic | ID | Status | Data Início | Data Fim | Progresso |
|------|-----|--------|-------------|-----------|-----------|
| Epic 0: Preparação e decisões base | GT-5 | ✅ Concluído | 12/01/2026 | 05/01/2026 | 100% |
| Epic 1: Bootstrap do repositório | GT-11 | ✅ Concluído | 12/01/2026 | 12/01/2026 | 100% |
| Epic 2: Database Schema Supabase | GT-17 | ✅ Concluído | 12/01/2026 | 19/01/2026 | 100% |
| Epic 3: Carga Inicial 600k Registros | GT-25 | 🔄 Em andamento | 19/01/2026 | 26/01/2026 | 80% |
| Epic 4: API Externa + Job Semanal | GT-219 | ⏳ Planejado | 26/01/2026 | 02/02/2026 | 0% |

### 🔵 FASE 1: CORE PLATFORM (Épicos 5-7)
**Período:** 02/02/2026 → 23/02/2026 (3 semanas)

Esta fase implementa a plataforma core, incluindo MCP Server, Agente LangGraph e integração com WhatsApp.

| Epic | ID | Status | Data Início | Data Fim | Progresso |
|------|-----|--------|-------------|-----------|-----------|
| Epic 5: MCP Server (FastAPI-MCP) | GT-38 | ⏳ Planejado | 02/02/2026 | 09/02/2026 | 0% |
| Epic 6: Agente (LangGraph) especializado | GT-40 | ⏳ Planejado | 09/02/2026 | 16/02/2026 | 0% |
| Epic 7: WhatsApp Evolution API | GT-188 | ⏳ Planejado | 16/02/2026 | 23/02/2026 | 0% |

### 🟢 FASE 2: ENHANCEMENTS (Épicos 8-9)
**Período:** 23/02/2026 → 16/03/2026 (3 semanas)

Esta fase adiciona funcionalidades de enriquecimento e monitoring.

| Epic | ID | Status | Data Início | Data Fim | Progresso |
|------|-----|--------|-------------|-----------|-----------|
| Epic 8: APIs Enriquecimento (CEP/CNPJ) | GT-195 | ⏳ Planejado | 23/02/2026 | 02/03/2026 | 0% |
| Epic 9: Monitoring Phoenix + Grafana Alloy | GT-201 | ⏳ Planejado | 02/03/2026 | 09/03/2026 | 0% |

### 🟡 FASE 3: PRODUCTION READY (Épicos 10-12)
**Período:** 09/03/2026 → 30/03/2026 (3 semanas)

Esta fase prepara o projeto para produção com deploy, multi-tenant, billing e analytics.

| Epic | ID | Status | Data Início | Data Fim | Progresso |
|------|-----|--------|-------------|-----------|-----------|
| Epic 10: Deploy VPS Coolify Production | GT-206 | ⏳ Planejado | 09/03/2026 | 16/03/2026 | 0% |
| Epic 11: Multi-tenant + Billing | GT-210 | ⏳ Planejado | 16/03/2026 | 23/03/2026 | 0% |
| Epic 12: Analytics + Lead Scoring | GT-213 | ⏳ Planejado | 23/03/2026 | 30/03/2026 | 0% |

---

## 📊 Progresso Geral

### Status dos Épicos

| Status | Quantidade | Porcentagem |
|--------|------------|-------------|
| ✅ Concluído | 3 | 25% |
| 🔄 Em andamento | 1 | 8% |
| ⏳ Planejado | 8 | 67% |

### Progresso por Fase

| Fase | Progresso | Status |
|------|-----------|--------|
| 🟣 FASE 0: Foundation - Data | 80% | 🔄 Em andamento |
| 🔵 FASE 1: Core Platform | 0% | ⏳ Planejado |
| 🟢 FASE 2: Enhancements | 0% | ⏳ Planejado |
| 🟡 FASE 3: Production Ready | 0% | ⏳ Planejado |

---

## 🎯 Próximos Passos Imediatos

### Prioridade Alta (Esta Semana)

1. **Concluir Epic 3: Carga Inicial 600k Registros**
   - Executar carga completa de 974k registros
   - Validar integridade dos dados
   - Gerar relatório de qualidade

2. **Iniciar Epic 4: API Externa + Job Semanal**
   - Implementar HubQuestClient (httpx async)
   - Implementar paginação robusta
   - Implementar retry/backoff + timeouts
   - Implementar job incremental semanal (APScheduler)
   - Criar scheduler container + comando manual sync
   - Teste integrado: client + paginação + upsert

### Prioridade Média (Próximas 2 Semanas)

3. **Iniciar Epic 5: MCP Server (FastAPI-MCP)**
   - Configurar FastAPI + MCP Server base
   - Implementar tools MCP (search_vehicles, get_stats, find_leads)
   - Cache Redis + validação de guardrails
   - Autenticação + allowlist de usuários
   - Testes unitários + integração MCP
   - Documentação API + exemplo Claude Desktop

4. **Iniciar Epic 6: Agente (LangGraph) especializado**
   - Criar StateGraph com 3 nós (intenção, seleção, execução)
   - Integrar MCP client no agente
   - Memory persistente Supabase
   - Fallback + human-in-loop
   - Testes e tracing LangSmith
   - Documentação agente + exemplos

---

## 📝 Notas Importantes

### Dependências entre Épicos

- **Epic 3** depende de **Epic 2** (Database Schema)
- **Epic 4** depende de **Epic 3** (Carga Inicial)
- **Epic 5** depende de **Epic 2** (Database Schema)
- **Epic 6** depende de **Epic 5** (MCP Server)
- **Epic 7** depende de **Epic 6** (Agente LangGraph)
- **Epic 8** depende de **Epic 5** (MCP Server)
- **Epic 9** depende de **Epic 5** (MCP Server)
- **Epic 10** depende de **Epic 5** (MCP Server)
- **Epic 11** depende de **Epic 10** (Deploy)
- **Epic 12** depende de **Epic 10** (Deploy)

### Riscos Identificados

1. **Timeout do Supabase:** A carga completa de 974k registros pode causar timeout. Solução: Usar batch inserts otimizados e processamento incremental.

2. **Performance do ETL:** O pipeline ETL precisa ser otimizado para processar 974k registros em tempo razoável. Solução: Scripts otimizados já criados e testados.

3. **Integração com API Externa:** A API externa pode ter limites de rate limiting e instabilidade. Solução: Implementar retry com exponential backoff e circuit breaker.

4. **Complexidade do Agente LangGraph:** O agente precisa ser robusto e lidar com múltiplas intenções. Solução: Implementar fallback + human-in-loop para casos de baixa confiança.

---

## 📚 Documentos Relacionados

- [`docs/EPICS.md`](docs/EPICS.md) - Detalhes de todos os épicos
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Status atual do projeto
- [`docs/architecture.md`](docs/architecture.md) - Arquitetura do projeto
- [`docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md`](docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md) - Respostas às perguntas sobre integrações

---

## 🔗 Links Externos

- **Linear Project:** https://linear.app/gtaitson/project/fleetintel-mcp-bfa0ee37e5f8
- **GitHub Repository:** https://github.com/Guitaitson/fleetintel-mcp
- **Supabase Project:** PostgreSQL 17.6 em `aws-1-us-east-1.pooler.supabase.com`

---

**Última Atualização:** 2026-02-02 18:56 BRT
