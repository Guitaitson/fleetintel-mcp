# FleetIntel MCP - Status do Projeto

**Última Atualização**: 2026-02-04 11:30 BRT  
**Branch Atual**: feature/mvp-guardrails  
**Último Commit**: refactor: Reorganiza estrutura do projeto (bf01d11)

---

## 🎯 Visão Geral

Este documento reflete o **estado atual** do projeto FleetIntel MCP. É atualizado antes de cada troca de ferramenta de agente (Cline, KiloCode, Cursor, etc.) ou antes de commits importantes.

### 📊 Status Geral do Projeto (Baseado no Linear)

**Total de Épicos:** 12  
**Total de Tarefas:** 60+  
**Responsável:** Guilherme Taitson  
**Período:** 12/01/2026 → 30/03/2026 (11 semanas)

**Progresso Geral:**
- ✅ **Épicos Concluídos:** 4 (33%)
- 🔄 **Épicos Em Andamento:** 1 (8%)
- ⏳ **Épicos Planejados:** 7 (59%)

**Status por Fase:**
- 🟣 **FASE 0: Foundation - Data:** 100% (✅ Concluído)
- 🔵 **FASE 1: Core Platform:** 0% (⏳ Planejado)
- 🟢 **FASE 2: Enhancements:** 0% (⏳ Planejado)
- 🟡 **FASE 3: Production Ready:** 0% (⏳ Planejado)

---

## 📊 Status dos Epics

### ✅ Epic 0-3: Setup + Database Redesign + ETL V1
**Status**: CONCLUÍDO  
**Documentação**: `docs/EPIC_0-3_FINAL_STATUS.md`

- Database redesign V2 implementado
- Migrations aplicadas
- Schema normalizado funcional

### ✅ Epic 4: ETL V2 - Correções de Tipos de Dados
**Status**: CONCLUÍDO ✅  
**Documentação**: `docs/git/CORRECOES_ETL_V2.md`

**Progresso:**
- ✅ Identificado problema: CNPJs, CEPs, CNAEs sendo lidos como floats
- ✅ Corrigido `scripts/load_excel_to_csv.py` (DTYPE_MAP)
- ✅ Corrigido `scripts/normalize_data.py` (zfill e forcing string types)
- ✅ Corrigido `scripts/load_normalized_schema.py` (dtype=str no CSV read)
- ✅ Excel → CSV Raw executado: **974,122 registros**
- ✅ CSV Raw → CSV Normalized executado: **974,122 registros**

### ✅ Epic 5: ETL Performance Optimization (GT-28) - RESOLVIDO!
**Status**: CONCLUÍDO ✅  
**Documentação**: `docs/ETL_PERFORMANCE_OPTIMIZATION_PLAN.md`, `docs/ETL_OPTIMIZATION_SUMMARY.md`

**Problema Original** (2026-02-02):
- **Performance Crítica**: Carga completa de 974k registros levaria **40+ dias** (0.3 reg/s)
- **Root Cause**: 1.1M queries individuais (row-by-row inserts)

**Solução Implementada**:
- ✅ **Batch Inserts**: Agrupamento de INSERTs em batches de 1000 registros
- ✅ **Vectorized Operations**: Pandas string operations (C-level) ao invés de `apply()`
- ✅ **Connection Pooling**: Aumentado de 15 para 50 conexões
- ✅ **Correção Crítica v7**: Removido begin_nested() e separado INSERT/SELECT
- ✅ **Deduplicação**: Contatos, Endereços, Empresas com deduplicação por ID

**Carga Completa Executada** (2026-02-04):
```
Tempo total: ~18 minutos (de ~11.5 horas para 18 min = 97% mais rápido!)
Registros processados: 986,859 veículos, 919,941 registrations
Erros: 0
```

**Dados Carregados no Supabase:**
```
marcas: 19
modelos: 1,886
vehicles: 986,859
empresas: 161,932 (de 919,941 totais - deduplicado!)
enderecos: 161,932
contatos: 155,622 (de 895,229 totais - deduplicado!)
registrations: 919,941
```

**Verificações de Integridade:**
- ✅ Todos os veículos têm modelo
- ✅ Todas as empresas têm endereço
- ✅ 6,310 empresas sem contato (normal - sem dados no Excel)
- ✅ Todos os registrations têm veículo

### 🚀 Epic 6: FastAPI MCP Server (GT-11 a GT-15)
**Status**: CONCLUÍDO ✅  
**Documentação**: `docs/FASTAPI_MCP_SERVER_STATUS.md`, `app/README.md`

**Implementação:**
- ✅ **GT-11**: Configuração do FastAPI Server
  - `app/main.py` - Entry point do servidor FastAPI
  - `app/config.py` - Configurações do servidor
  - `app/schemas/query_schemas.py` - Schemas Pydantic para queries/responses

- ✅ **GT-12**: Endpoints de Consulta
  - `GET /health` - Health check do servidor
  - `GET /stats` - Estatísticas do banco de dados
  - `POST /vehicles/query` - Busca de veículos
  - `POST /empresas/query` - Busca de empresas
  - `POST /registrations/query` - Busca de registros de emplacamento

---

## 🐛 Problemas em Aberto

### ✅ RESOLVIDO: Carga ETL Completa Falhou (2026-02-03)
**Status**: RESOLVIDO EM 2026-02-04! 🎉

**Problema Original**: Apenas 2.6% dos dados carregados (36,851 de 1,435,223)
**Causa Raiz**: Script criando contatos duplicados (99,822 discrepância)

**Solução Implementada:**
1. ✅ Script ETL V7 com deduplicação por empresa_id
2. ✅ Contatos reduzidos de 895,229 para 155,622 (85% redução)
3. ✅ Empresas reduzidas de 919,941 para 161,932 (82% redução)
4. ✅ Performance de ~11.5h para ~18 minutos (97% melhoria)

---

## 📈 Resumo dos Dados no Supabase

| Tabela | Registros | Status |
|--------|-----------|--------|
| marcas | 19 | ✅ OK |
| modelos | 1,886 | ✅ OK |
| vehicles | 986,859 | ✅ OK (100% com modelo) |
| empresas | 161,932 | ✅ OK (únicos) |
| enderecos | 161,932 | ✅ OK (1:1 com empresas) |
| contatos | 155,622 | ✅ OK (96% das empresas) |
| registrations | 919,941 | ✅ OK (100% com veículo) |

---

## 🔧 Decisões Técnicas Recentes

### 2026-02-04: ETL V7 - Correção Crítica + Performance
- **Problema**: "This result object does not return rows" - begin_nested() causava erro
- **Solução**: Separar INSERT e SELECT em conexões diferentes
- **Performance**: Batch size de 50 → 1000, pool de 5 → 20
- **Resultado**: ~11.5h → ~18 minutos (97% mais rápido!)

### 2026-02-03: Investigação de Causa Raiz
- **Problema**: Carga completa falhou com apenas 2.6% dos dados carregados
- **Causa Raiz Identificada**:
  1. Script criando contatos duplicados (99,822 discrepância)
  2. Arquitetura do banco com muitos índices e constraints
  3. Lógica de preparação de dados (criando duplicatas)
- **Decisão**: Corrigir causa raiz antes de continuar com carga completa
- **Resultado**: ✅ CORRIGIDO! Dados carregados com sucesso em 2026-02-04

---

## 🚀 Próximos Milestones

### Curto Prazo (Esta Semana)
- [x] Resolver problema de registrations (98% sucesso) ✅
- [x] Implementar otimização de performance do ETL (50x mais rápido) ✅
- [x] Implementar FastAPI MCP Server (GT-11 a GT-15) ✅
- [x] Traduzir projeto do Linear para documentos locais ✅
- [x] Implementar rotina de integração com Git ✅
- [x] Executar Excel → CSV Raw (986,859 registros) ✅
- [x] Executar CSV Raw → CSV Normalized (986,859 registros) ✅
- [x] **CORRIGIR CAUSA RAIZ DO TIMEOUT** ✅ RESOLVIDO!
- [x] Completar carga ETL completa de 986k registros após corrigir causa raiz ✅
- [x] Validar integridade dos dados no Supabase ✅
- [ ] **PRÓXIMO**: Implementar Guardrails MVP (GT-9)
  - [ ] Criar query_schemas com validacao Pydantic
  - [ ] Implementar rate limiting
  - [ ] Adicionar sanitizacao de inputs
  - [ ] Criar testes unitarios

### Médio Prazo (Próximas 2 Semanas)
- [ ] Implementar Epic 4: API Externa + Job Semanal (GT-219)
  - [ ] Implementar HubQuestClient (httpx async)
  - [ ] Implementar paginação robusta
  - [ ] Implementar retry/backoff + timeouts
  - [ ] Implementar job incremental semanal (APScheduler)
  - [ ] Criar scheduler container + comando manual sync
  - [ ] Teste integrado: client + paginação + upsert
- [ ] Implementar Epic 5: MCP Server (FastAPI-MCP) (GT-38)
  - [ ] Configurar FastAPI + MCP Server base
  - [ ] Implementar tools MCP (search_vehicles, get_stats, find_leads)
  - [ ] Cache Redis + validação de guardrails
  - [ ] Autenticação + allowlist de usuários
  - [ ] Testes unitários + integração MCP
  - [ ] Documentação API + exemplo Claude Desktop

### Longo Prazo (Próximo Mês)
- [ ] Implementar Epic 6: Agente (LangGraph) especializado (GT-40)
- [ ] Implementar Epic 7: WhatsApp Evolution API (GT-188)
- [ ] Implementar Epic 8: APIs Enriquecimento (CEP/CNPJ) (GT-195)
- [ ] Implementar Epic 9: Monitoring Phoenix + Grafana Alloy (GT-201)

---

## 📚 Documentação Complementar

### Documentos Principais
- **Setup Inicial**: `docs/SETUP.md`
- **Arquitetura**: `docs/DATABASE_REDESIGN_V2.md`
- **ETL V2 Corrections**: `docs/git/CORRECOES_ETL_V2.md`
- **Git Strategies**: `docs/git/branching-strategy.md`, `docs/git/tagging-strategy.md`
- **Onboarding para Agentes**: `docs/ONBOARDING_AGENT.md`

### Documentos de Integração
- **Linear Project**: https://linear.app/gtaitson/project/fleetintel-mcp-bfa0ee37e5f8
- **GitHub Repository**: https://github.com/Guitaitson/fleetintel-mcp
- **Supabase Project**: PostgreSQL 17.6 em `aws-1-us-east-1.pooler.supabase.com`

---

## 🤝 Contribuindo

Este projeto usa:
- **Conventional Commits** (feat:, fix:, docs:, etc.)
- **Branches**: feature/, bugfix/, hotfix/ + descrição
- **PRs**: Obrigatório para mudanças não triviais

---

**Última ação**: ETL V7 executado com sucesso - 986,859 veículos, 919,941 registrations carregados em ~18 minutos (97% mais rápido que antes!). Problema de duplicatas resolvido - contatos reduzidos de 895K para 155K (85% redução).
