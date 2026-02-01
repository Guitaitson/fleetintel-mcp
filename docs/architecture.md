# Arquitetura FleetIntel MCP

## Visão Geral

Sistema de consulta inteligente de dados de frota brasileira, expondo API MCP para integração com LLMs.

## Componentes

### 1. Data Layer (Supabase Postgres)
- Tabelas: `registrations`, `sync_logs`
- Índices: datas, placas, CPFs
- Row Level Security (futuro)

### 2. Cache Layer (Redis)
- TTL queries: 5 minutos
- Session data: agente conversacional
- Job locks: sincronização

### 3. MCP Server (FastAPI)
- Endpoints RESTful (JSON-RPC futuro)
- Paginação: cursor-based
- Rate limit: 100 req/min por IP

### 4. Agent Layer (LangGraph)
- State: TypedDict com histórico
- Tools: endpoints MCP server
- LLM: OpenAI GPT-4o-mini

### 5. Jobs Layer
- Sync incremental: Domingo 22h
- Cleanup cache: Diário 3h
- Health checks: A cada 5min

## Fluxo de Dados

API Externa (HubQuest)
↓ (jobs/sync)
Supabase Postgres ←→ Redis (cache)
↓ (queries)
MCP Server (FastAPI)
↓ (tools)
LangGraph Agent
↓ (respostas)
Cliente (Claude Desktop, etc)

## Decisões Arquiteturais

### ADR-001: Supabase ao invés de Postgres local
**Contexto**: VPS com 2.5GB RAM limitado
**Decisão**: Usar Supabase gerenciado
**Consequências**: 
- (+) Menos overhead no VPS
- (+) Backups automáticos
- (-) Latência inter-região (~50ms)

### ADR-002: Sincronização semanal (não diária)
**Contexto**: API com warm-up lento, dados pouco voláteis
**Decisão**: Sync domingo 22h com janela 8 dias
**Consequências**:
- (+) Menor carga na API externa
- (-) Dados podem ter até 7 dias de defasagem

### ADR-003: Redis local no Docker
**Contexto**: Cache deve ser rápido (<5ms)
**Decisão**: Redis no mesmo VPS
**Consequências**:
- (+) Latência mínima
- (-) Consome ~50MB RAM
