# Épicos do FleetIntel MCP

**Versão:** 1.0.0  
**Data:** 2026-02-02  
**Status:** Em andamento

---

## 📋 Visão Geral

Este documento contém detalhes completos de todos os 12 épicos do projeto FleetIntel MCP, organizados por fase e ordem de implementação.

**Total de Épicos:** 12  
**Total de Tarefas:** 60+  
**Responsável:** Guilherme Taitson

---

## 🟣 FASE 0: FOUNDATION - DATA (Épicos 0-4)

### Epic 0: Preparação e decisões base

**ID:** GT-5  
**Status:** ✅ Concluído  
**Período:** 12/01/2026 → 05/01/2026  
**Prioridade:** Urgente

**Descrição:**
Fase inicial de decisões arquiteturais: repositório, ambientes, fonte de verdade (Supabase), escopo MVP e política de atualização. Este épico define as fundações do projeto antes de iniciar desenvolvimento técnico.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-6 | 0.1: Definir repositório (GitHub) + estratégia de branches + tags para rollback | ✅ Concluído | 3 Points |
| GT-7 | 0.2: Definir ambientes (local, staging, prod) + naming .env | ✅ Concluído | 2 Points |
| GT-8 | 0.3: Definir fonte de verdade: Supabase + Redis | ✅ Concluído | 3 Points |
| GT-9 | 0.4: Definir escopo MVP + guardrails de consultas | ✅ Concluído | 3 Points |
| GT-10 | 0.5: Definir política de atualização incremental semanal | ✅ Concluído | 3 Points |

**Resultados:**
- ✅ Repositório GitHub criado com estratégia de branches (main, dev, feature/*)
- ✅ Ambientes definidos (local, staging, prod) com .env.example
- ✅ Supabase definido como fonte de verdade + Redis para cache
- ✅ Escopo MVP definido com guardrails de consultas
- ✅ Política de atualização incremental semanal definida

---

### Epic 1: Bootstrap do repositório e infraestrutura local

**ID:** GT-11  
**Status:** ✅ Concluído  
**Período:** 12/01/2026 → 12/01/2026  
**Prioridade:** Urgente

**Descrição:**
Configuração completa do projeto: estrutura de diretórios, dependências Python, variáveis de ambiente, Docker local e Makefile para facilitar desenvolvimento.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-12 | 1.1: Criar estrutura de diretórios do projeto | ✅ Concluído | 1 Point |
| GT-13 | 1.2: Criar requirements.txt + pyproject.toml + lock file | ✅ Concluído | 2 Points |
| GT-14 | 1.3: Criar .env.example com todas as chaves | ✅ Concluído | 1 Point |
| GT-15 | 1.4: Criar docker-compose.local.yml | ✅ Concluído | 2 Points |
| GT-16 | 1.5: Criar Makefile com comandos essenciais | ✅ Concluído | 2 Points |

**Resultados:**
- ✅ Estrutura de diretórios criada (mcp_server/, agent/, jobs/, scripts/, deploy/, tests/, docs/)
- ✅ Dependências Python configuradas com pyproject.toml e requirements.txt
- ✅ .env.example criado com todas as variáveis necessárias
- ✅ docker-compose.local.yml criado com Redis local
- ✅ Makefile criado com comandos essenciais (install, dev, test, lint, format, logs, stop)

---

### Epic 2: Fonte de verdade (Supabase Postgres)

**ID:** GT-17  
**Status:** ✅ Concluído  
**Período:** 12/01/2026 → 19/01/2026  
**Prioridade:** Urgente

**Descrição:**
Configuração completa do banco de dados Supabase como fonte de verdade do projeto. Inclui schema, índices, tabelas auxiliares, materialized views e estratégia de manutenção.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-18 | 2.1: Criar projeto Supabase + configurar acesso | ✅ Concluído | 1 Point |
| GT-19 | 2.2: Criar migração registrations (schema + tipos) | ✅ Concluído | 3 Points |
| GT-20 | 2.3: Definir chave única + deduplicação (UNIQUE constraint) | ✅ Concluído | 2 Points |
| GT-21 | 2.4: Criar índices mínimos para performance | ✅ Concluído | 2 Points |
| GT-22 | 2.5: Criar tabelas auxiliares (checkpoints, auth_sessions, audit_logs) | ✅ Concluído | 3 Points |
| GT-23 | 2.6: Criar materialized views + índices + refresh strategy | ✅ Concluído | 4 Points |
| GT-24 | 2.7: Rotina de manutenção DB (ANALYZE, monitoring) | ✅ Concluído | 2 Points |

**Resultados:**
- ✅ Projeto Supabase criado e configurado
- ✅ Schema registrations criado com tipos apropriados
- ✅ Chave única definida para deduplicação
- ✅ Índices criados para performance
- ✅ Tabelas auxiliares criadas (checkpoints, auth_sessions, audit_logs)
- ✅ Materialized views criadas com refresh strategy
- ✅ Rotina de manutenção DB configurada

---

### Epic 3: Carga Inicial 600k Registros

**ID:** GT-25  
**Status:** 🔄 Em andamento (80%)  
**Período:** 19/01/2026 → 26/01/2026  
**Prioridade:** Urgente

**Descrição:**
Pipeline de carga inicial: script de ingestão em batch (10k registros/batch), validação de dados (schema Pydantic, duplicatas por placa+renavam), logs estruturados e métricas de progresso, idempotência e resume, rollback strategy (snapshot antes da carga), testes com subset 10k antes do full load.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-26 | 3.1: Pipeline Excel → CSV padronizado | ✅ Concluído | 2 Points |
| GT-27 | 3.2: Normalização/limpeza de dados | ✅ Concluído | 3 Points |
| GT-28 | 3.3: Importação para Supabase (upsert + logs) | ✅ Concluído | 3 Points |
| GT-29 | 3.4: Pós-carga: validação e refresh views | ✅ Concluído | 2 Points |
| GT-30 | 3.5: Quality report (% null, datas inválidas, duplicatas) | ✅ Concluído | 2 Points |

**Resultados:**
- ✅ Pipeline Excel → CSV padronizado implementado
- ✅ Normalização/limpeza de dados implementada
- ✅ Importação para Supabase com upsert + logs implementada
- ✅ Pós-carga: validação e refresh views implementado
- ✅ Quality report implementado
- ⚠️ Carga completa de 974k registros NÃO executada (timeout do Supabase)

**Próximos Passos:**
- Executar carga completa de 974k registros com scripts otimizados
- Validar integridade dos dados
- Gerar relatório de qualidade final

---

### Epic 4: API Externa + Job Semanal Incremental

**ID:** GT-219  
**Status:** ⏳ Planejado  
**Período:** 26/01/2026 → 02/02/2026  
**Prioridade:** Urgente

**Descrição:**
Cliente HTTP robusto para API externa: retry com exponential backoff, timeout configurável, autenticação. Job incremental semanal (cron/Temporal/n8n): busca apenas registros novos desde último sync (watermark em sync_logs), deduplicação inteligente (merge por placa+renavam), upsert otimizado em Supabase, monitoramento de sync (alertas falhas, latency, registros processados).

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-32 | 4.1: Implementar HubQuestClient (httpx async) | ⏳ Planejado | 3 Points |
| GT-33 | 4.2: Paginação robusta + limites (1000 rows, 90 dias) | ⏳ Planejado | 2 Points |
| GT-34 | 4.3: Retry/backoff + timeouts + warm-up | ⏳ Planejado | 2 Points |
| GT-35 | 4.4: Job incremental semanal (APScheduler) | ⏳ Planejado | 3 Points |
| GT-36 | 4.5: Scheduler container + comando manual sync | ⏳ Planejado | 2 Points |
| GT-37 | 4.6: Teste integrado: client + paginação + upsert | ⏳ Planejado | 3 Points |

**Próximos Passos:**
- Implementar HubQuestClient com httpx async
- Implementar paginação robusta com limites
- Implementar retry/backoff + timeouts + warm-up
- Implementar job incremental semanal com APScheduler
- Criar scheduler container + comando manual sync
- Teste integrado: client + paginação + upsert

---

## 🔵 FASE 1: CORE PLATFORM (Épicos 5-7)

### Epic 5: MCP Server (FastAPI-MCP) baseado em Postgres

**ID:** GT-38  
**Status:** ⏳ Planejado  
**Período:** 02/02/2026 → 09/02/2026  
**Prioridade:** Urgente

**Descrição:**
FastAPI + MCP server com tools para busca emplacamentos, estatisticas, leads. Cache Redis, autenticacao, rate limiting, guardrails.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-183 | 5.1: Configurar FastAPI + MCP Server base | ⏳ Planejado | 4 Points |
| GT-176 | 5.2: Implementar tools MCP (search_vehicles, get_stats, find_leads) | ⏳ Planejado | 3 Points |
| GT-177 | 5.3: Cache Redis + validação de guardrails | ⏳ Planejado | 3 Points |
| GT-178 | 5.4: Autenticação + allowlist de usuários | ⏳ Planejado | 2 Points |
| GT-179 | 5.5: Testes unitários + integração MCP | ⏳ Planejado | 3 Points |
| GT-180 | 5.6: Documentação API + exemplo Claude Desktop | ⏳ Planejado | 2 Points |

**Próximos Passos:**
- Configurar FastAPI + MCP Server base
- Implementar tools MCP (search_vehicles, get_stats, find_leads)
- Implementar cache Redis + validação de guardrails
- Implementar autenticação + allowlist de usuários
- Criar testes unitários + integração MCP
- Documentar API + exemplo Claude Desktop

---

### Epic 6: Agente (LangGraph) especializado

**ID:** GT-40  
**Status:** ⏳ Planejado  
**Período:** 09/02/2026 → 16/02/2026  
**Prioridade:** Urgente

**Descrição:**
StateGraph com intenção→seleção→execução. Persistência memória, guardrails, rate limit LLM.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-181 | 6.1: Criar StateGraph com 3 nós (intenção, seleção, execução) | ⏳ Planejado | 4 Points |
| GT-182 | 6.2: Integrar MCP client no agente | ⏳ Planejado | 3 Points |
| GT-184 | 6.3: Memory persistente Supabase | ⏳ Planejado | 3 Points |
| GT-185 | 6.4: Fallback + human-in-loop | ⏳ Planejado | 2 Points |
| GT-186 | 6.5: Testes e tracing LangSmith | ⏳ Planejado | 2 Points |
| GT-187 | 6.6: Documentação agente + exemplos | ⏳ Planejado | 1 Point |

**Próximos Passos:**
- Criar StateGraph com 3 nós (intenção, seleção, execução)
- Integrar MCP client no agente
- Implementar memory persistente Supabase
- Implementar fallback + human-in-loop
- Criar testes e tracing LangSmith
- Documentar agente + exemplos

---

### Epic 7: WhatsApp Evolution API

**ID:** GT-188  
**Status:** ⏳ Planejado  
**Período:** 16/02/2026 → 23/02/2026  
**Prioridade:** Urgente

**Descrição:**
Integração Evolution API com MCP Server, webhooks, persistência, rate limiting.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-189 | 7.1: Configurar Evolution API instance | ⏳ Planejado | 2 Points |
| GT-190 | 7.2: Webhook handler LangGraph | ⏳ Planejado | 4 Points |
| GT-191 | 7.3: Persistência mensagens Supabase | ⏳ Planejado | 2 Points |
| GT-192 | 7.4: Typing indicators + read receipts | ⏳ Planejado | 1 Point |
| GT-193 | 7.5: Rate limiting por WhatsApp ID | ⏳ Planejado | 2 Points |
| GT-194 | 7.6: Testes E2E WhatsApp flow | ⏳ Planejado | 3 Points |

**Próximos Passos:**
- Configurar Evolution API instance
- Implementar webhook handler LangGraph
- Implementar persistência mensagens Supabase
- Implementar typing indicators + read receipts
- Implementar rate limiting por WhatsApp ID
- Criar testes E2E WhatsApp flow

---

## 🟢 FASE 2: ENHANCEMENTS (Épicos 8-9)

### Epic 8: APIs Enriquecimento (CEP/CNPJ)

**ID:** GT-195  
**Status:** ⏳ Planejado  
**Período:** 23/02/2026 → 02/03/2026  
**Prioridade:** Urgente

**Descrição:**
Integração BrasilAPI CEP V2 + CNPJ, enriquecimento automático, composite tools, fallbacks e circuit breakers.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-196 | 8.1: BrasilAPI CEP V2 tools | ⏳ Planejado | 2 Points |
| GT-197 | 8.2: BrasilAPI CNPJ tool completa | ⏳ Planejado | 3 Points |
| GT-198 | 8.3: Enrichment pipeline automático | ⏳ Planejado | 3 Points |
| GT-199 | 8.4: Composite tools (veículos + CEP/CNPJ) | ⏳ Planejado | 3 Points |
| GT-200 | 8.5: Rate limiting BrasilAPI | ⏳ Planejado | 2 Points |

**Próximos Passos:**
- Implementar BrasilAPI CEP V2 tools
- Implementar BrasilAPI CNPJ tool completa
- Implementar enrichment pipeline automático
- Implementar composite tools (veículos + CEP/CNPJ)
- Implementar rate limiting BrasilAPI

---

### Epic 9: Monitoring Phoenix + Grafana Alloy

**ID:** GT-201  
**Status:** ⏳ Planejado  
**Período:** 02/03/2026 → 09/03/2026  
**Prioridade:** Urgente

**Descrição:**
Phoenix observability stack, traces LangGraph + MCP, métricas Redis/Supabase, dashboards essenciais, alertas críticos.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-202 | 9.1: Phoenix observability stack | ⏳ Planejado | 4 Points |
| GT-203 | 9.2: Grafana Alloy agent VPS | ⏳ Planejado | 3 Points |
| GT-204 | 9.3: Dashboards essenciais | ⏳ Planejado | 3 Points |
| GT-205 | 9.4: Alertas Phoenix | ⏳ Planejado | 2 Points |

**Próximos Passos:**
- Implementar Phoenix observability stack
- Implementar Grafana Alloy agent VPS
- Criar dashboards essenciais
- Configurar alertas Phoenix

---

## 🟡 FASE 3: PRODUCTION READY (Épicos 10-12)

### Epic 10: Deploy VPS Coolify Production

**ID:** GT-206  
**Status:** ⏳ Planejado  
**Período:** 09/03/2026 → 16/03/2026  
**Prioridade:** Urgente

**Descrição:**
Docker multi-stage MCP Server (<100MB), Coolify production stack (Redis + Grafana Alloy), env vars Infisical, auto-deploy GitHub, zero-downtime deployments com health checks.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-207 | 10.1: Docker multi-stage MCP Server | ⏳ Planejado | 3 Points |
| GT-208 | 10.2: Coolify production stack | ⏳ Planejado | 3 Points |
| GT-209 | 10.3: Zero-downtime deployments | ⏳ Planejado | 2 Points |
| GT-220 | 10.4: Secrets management com Infisical | ⏳ Planejado | 3 Points |
| GT-221 | 10.5: Backup automático Supabase + Redis | ⏳ Planejado | 2 Points |
| GT-222 | 10.6: Hardening VPS + Security Best Practices | ⏳ Planejado | 3 Points |

**Próximos Passos:**
- Implementar Docker multi-stage MCP Server
- Implementar Coolify production stack
- Implementar zero-downtime deployments
- Implementar secrets management com Infisical
- Implementar backup automático Supabase + Redis
- Implementar hardening VPS + Security Best Practices

---

### Epic 11: Multi-tenant + Billing

**ID:** GT-210  
**Status:** ⏳ Planejado  
**Período:** 16/03/2026 → 23/03/2026  
**Prioridade:** Urgente

**Descrição:**
Tenant isolation com Supabase Row Level Security (RLS), tenant_id em todas tabelas, Stripe billing integration com usage-based pricing (requests MCP + BrasilAPI), webhooks, tenant quotas.

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-211 | 11.1: Tenant isolation Supabase Row Level Security | ⏳ Planejado | 4 Points |
| GT-212 | 11.2: Stripe billing integration | ⏳ Planejado | 4 Points |

**Próximos Passos:**
- Implementar tenant isolation Supabase Row Level Security
- Implementar Stripe billing integration

---

### Epic 12: Analytics + Lead Scoring

**ID:** GT-213  
**Status:** ⏳ Planejado  
**Período:** 23/03/2026 → 30/03/2026  
**Prioridade:** Urgente

**Descrição:**
Analytics dashboard por tenant (usage stats, top queries, fleet insights, export CSV/PDF), lead scoring automático (score empresas por frota + CEP + porte CNPJ, priorização leads quentes).

**Tarefas:**

| ID | Tarefa | Status | Estimativa |
|----|--------|--------|-------------|
| GT-214 | 12.1: Analytics dashboard tenant | ⏳ Planejado | 3 Points |
| GT-215 | 12.2: Lead scoring automático | ⏳ Planejado | 3 Points |

**Próximos Passos:**
- Implementar analytics dashboard tenant
- Implementar lead scoring automático

---

## 📊 Resumo dos Épicos

### Status por Fase

| Fase | Épicos | Concluídos | Em Andamento | Planejados | Progresso |
|------|---------|-------------|---------------|-------------|-----------|
| 🟣 FASE 0: Foundation - Data | 5 | 3 | 1 | 1 | 80% |
| 🔵 FASE 1: Core Platform | 3 | 0 | 0 | 3 | 0% |
| 🟢 FASE 2: Enhancements | 2 | 0 | 0 | 2 | 0% |
| 🟡 FASE 3: Production Ready | 3 | 0 | 0 | 3 | 0% |

### Estimativa de Esforço

| Fase | Estimativa Total (Points) | Status |
|------|-------------------------|--------|
| 🟣 FASE 0: Foundation - Data | 47 Points | 🔄 Em andamento |
| 🔵 FASE 1: Core Platform | 42 Points | ⏳ Planejado |
| 🟢 FASE 2: Enhancements | 26 Points | ⏳ Planejado |
| 🟡 FASE 3: Production Ready | 36 Points | ⏳ Planejado |
| **TOTAL** | **151 Points** | **25% Concluído** |

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

- [`docs/ROADMAP.md`](docs/ROADMAP.md) - Roadmap completo do projeto
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Status atual do projeto
- [`docs/architecture.md`](docs/architecture.md) - Arquitetura do projeto
- [`docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md`](docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md) - Respostas às perguntas sobre integrações

---

## 🔗 Links Externos

- **Linear Project:** https://linear.app/gtaitson/project/fleetintel-mcp-bfa0ee37e5f8
- **GitHub Repository:** https://github.com/Guitaitson/fleetintel-mcp
- **Supabase Project:** PostgreSQL 17.6 em `aws-1-us-east-1.pooler.supabase.com`

---

**Última Atualização:** 2026-02-02 18:57 BRT
