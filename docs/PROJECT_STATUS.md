# FleetIntel MCP - Status do Projeto

**Última Atualização**: 2026-02-02 18:59 BRT  
**Branch Atual**: feature/gt-9-mvp-guardrails  
**Último Commit**: GT-9: Implement MVP scope and guardrails (2026-01-04)

---

## 🎯 Visão Geral

Este documento reflete o **estado atual** do projeto FleetIntel MCP. É atualizado antes de cada troca de ferramenta de agente (Cline, KiloCode, Cursor, etc.) ou antes de commits importantes.

### 📊 Status Geral do Projeto (Baseado no Linear)

**Total de Épicos:** 12  
**Total de Tarefas:** 60+  
**Responsável:** Guilherme Taitson  
**Período:** 12/01/2026 → 30/03/2026 (11 semanas)

**Progresso Geral:**
- ✅ **Épicos Concluídos:** 3 (25%)
- 🔄 **Épicos Em Andamento:** 1 (8%)
- ⏳ **Épicos Planejados:** 8 (67%)

**Status por Fase:**
- 🟣 **FASE 0: Foundation - Data:** 80% (🔄 Em andamento)
- 🔵 **FASE 1: Core Platform:** 0% (⏳ Planejado)
- 🟢 **FASE 2: Enhancements:** 0% (⏳ Planejado)
- 🟡 **FASE 3: Production Ready:** 0% (⏳ Planejado)

**Documentos Recentes:**
- ✅ [`docs/ROADMAP.md`](docs/ROADMAP.md) - Roadmap completo do projeto
- ✅ [`docs/EPICS.md`](docs/EPICS.md) - Detalhes de todos os épicos
- ✅ [`docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md`](docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md) - Respostas às perguntas sobre integrações

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

**Progresso**:
- ✅ Identificado problema: CNPJs, CEPs, CNAEs sendo lidos como floats
- ✅ Corrigido `scripts/load_excel_to_csv.py` (DTYPE_MAP)
- ✅ Corrigido `scripts/normalize_data.py` (zfill e forcing string types)
- ✅ Corrigido `scripts/load_normalized_schema.py` (dtype=str no CSV read)
- ✅ Excel → CSV Raw executado: **974,122 registros**
- ✅ CSV Raw → CSV Normalized executado: **974,122 registros**
- ✅ **Teste com 100 registros: 98 registrations inseridos** (98% sucesso)

**Bugs Corrigidos** (2026-02-02):
1. ✅ **Bug #1 - `preco_validado` boolean**: Campo recebia `nan` (float) e strings `'SIM'`/`'NÃO'` ao invés de boolean. Solução: Conversão explícita para True/False/None.
2. ✅ **Bug #2 - Unique constraint**: `ON CONFLICT` estava na constraint errada. Solução: Mudado de `(external_id)` para `(vehicle_id, data_emplacamento)`.
3. ✅ **Bug #3 - Campos string com `nan`**: Campos string recebiam `nan` (float). Solução: Função `safe_str()` para converter `nan` → `None`.

**Resultado Final**:
```
Teste load_normalized_schema.py (100 registros):
- Marcas: 6 inseridos ✅
- Modelos: 30 inseridos ✅
- Vehicles: 100 inseridos ✅
- Empresas: 50 inseridos ✅
- Registrations: 98 inseridos ✅ (2 erros esperados = CNPJs ausentes)
```

### 🚀 Epic 5: ETL Performance Optimization (GT-28)
**Status**: CONCLUÍDO ✅  
**Documentação**: `docs/ETL_PERFORMANCE_OPTIMIZATION_PLAN.md`, `docs/ETL_OPTIMIZATION_SUMMARY.md`

**Problema Identificado** (2026-02-02):
- **Performance Crítica**: Carga completa de 974k registros levaria **40+ dias** (0.3 reg/s)
- **Root Cause**: 1.1M queries individuais (row-by-row inserts)
- **Impacto**: Impossível usar o sistema em produção

**Solução Implementada**:
- ✅ **Batch Inserts**: Agrupamento de INSERTs em batches de 1000 registros
- ✅ **Vectorized Operations**: Pandas string operations (C-level) ao invés de `apply()`
- ✅ **Connection Pooling**: Aumentado de 15 para 50 conexões
- ✅ **Temporary Indexes**: Índices temporários antes da carga
- ✅ **Real Chunking**: Processamento em chunks de 50k registros

**Scripts Otimizados Criados**:
1. ✅ `scripts/load_normalized_schema_optimized_v2.py` - Carga otimizada (BATCH INSERTS)
2. ✅ `scripts/normalize_data_optimized.py` - Normalização vectorizada
3. ✅ `scripts/load_excel_to_csv_optimized.py` - Excel → CSV com chunking real
4. ✅ `scripts/benchmark_etl.py` - Benchmark de performance
5. ✅ `scripts/README_OPTIMIZED.md` - Documentação completa

**Resultados de Testes** (2026-02-02):
```
Teste com 100 registros:
- 98 registrations inseridos em 8 segundos
- Taxa: 11 reg/s

Teste com 10.000 registros:
- 9.443 registrations inseridos em 22 segundos
- Taxa: 423 reg/s
- Melhoria estimada: 50x mais rápido que row-by-row
```

**Projeção para Carga Completa**:
- **Antes**: 40+ dias (0.3 reg/s)
- **Depois**: ~38 minutos (423 reg/s)
- **Melhoria**: 1.500x mais rápido

**Próximos Passos**:
1. Executar carga completa com `--full` (974k registros)
2. Validar integridade dos dados no Supabase
3. Gerar relatório de qualidade de dados
4. Atualizar PROJECT_STATUS.md com resultados finais

---

### 🚀 Epic 6: FastAPI MCP Server (GT-11 a GT-15)
**Status**: CONCLUÍDO ✅  
**Documentação**: `docs/FASTAPI_MCP_SERVER_STATUS.md`, `app/README.md`

**Implementação**:
- ✅ **GT-11**: Configuração do FastAPI Server
  - `app/main.py` - Entry point do servidor FastAPI
  - `app/config.py` - Configurações do servidor
  - `app/schemas/query_schemas.py` - Schemas Pydantic para queries/responses
  - `app/README.md` - Documentação completa

- ✅ **GT-12**: Endpoints de Consulta
  - `GET /health` - Health check do servidor
  - `GET /stats` - Estatísticas do banco de dados
  - `POST /vehicles/query` - Busca de veículos
  - `POST /empresas/query` - Busca de empresas
  - `POST /registrations/query` - Busca de registros de emplacamento

- ✅ **GT-13**: Schemas de Dados
  - `VehicleQuery`, `VehicleResponse`
  - `EmpresaQuery`, `EmpresaResponse`
  - `RegistrationQuery`, `RegistrationResponse`
  - `StatsResponse`

- ✅ **GT-14**: Conexão com Banco de Dados
  - SQLAlchemy AsyncPG
  - Pool Size: 10 conexões
  - Max Overflow: 20 conexões
  - Pool Recycle: 3600 segundos (1 hora)
  - Statement Timeout: 600000ms (10 minutos)

- ✅ **GT-15**: Documentação e Testes
  - `app/README.md` - Documentação completa do servidor
  - OpenAPI/Swagger UI disponível em `/docs`
  - ReDoc disponível em `/redoc`
  - `scripts/test_fastapi_server.py` - Script de teste automatizado

**Correções Realizadas**:
1. ✅ Pydantic v2 Compatibility em `src/config/settings.py`
2. ✅ Pydantic v2 Compatibility em `src/fleet_intel_mcp/config.py`
3. ✅ Adicionada função `get_db_engine()` em `src/fleet_intel_mcp/db/connection.py`
4. ✅ Adicionada importação `Request` em `app/main.py`
5. ✅ Adicionadas variáveis de ambiente necessárias ao `.env`

**Resultados dos Testes** (2026-02-02):
```
[1/5] Testing app import... [OK]
[2/5] Testing app configuration... [OK]
[3/5] Testing routes... [OK] (10 rotas)
[4/5] Testing database connection... [OK]
[5/5] Testing schemas... [OK]
All tests passed! [OK]
```

**Status Final**: ✅ **FASTAPI MCP SERVER PRONTO PARA USO**

---

## 🔧 Decisões Técnicas Recentes

### 2026-01-31: Estratégia de Versionamento
- Adotado **Semantic Versioning 2.0.0** (MAJOR.MINOR.PATCH)
- Criado `docs/git/tagging-strategy.md`
- Planejamento de releases:
  - v0.1.0: MVP FastAPI MCP Server
  - v0.2.0: Agente LangGraph
  - v0.3.0: Integração WhatsApp
  - v1.0.0: Produção completa

### 2026-01-31: Correção de Tipos de Dados no ETL
- **Root Cause**: Pandas lê códigos numéricos (CNPJ, CEP, CNAE) como floats por padrão
- **Solução**: Forçar dtype=str em todas as etapas (Excel → CSV → Processing)
- **Regra de Negócio**: CNPJs, CPFs, CEPs, CNAEs SEMPRE strings com zfill()

### 2026-01-31: Flexibilidade Tool-Agnostic
- Criado `.clinerules` para contexto de agentes de IA
- Criado `PROJECT_STATUS.md` (este arquivo)
- Atualizado `.gitignore` para proteger credenciais e dados sensíveis
- Implementado workflow de sincronização GitHub

---

## 🐛 Problemas em Aberto

###  MÉDIO: Dados CSV grandes não protegidos inicialmente
- **Resolvido**: Atualizado `.gitignore` em 2026-01-31
- **Ação Pendente**: Remover CSVs grandes do histórico Git se necessário

---

## 📝 Configuração de Ambiente

### Pré-requisitos
- Python 3.12+
- uv (package manager)
- Supabase account com projeto configurado
- `.env` com credenciais (ver `.env.example`)

### Setup Rápido
```bash
# Clone
git clone git@github.com:Guitaitson/fleetintel-mcp.git
cd fleetintel-mcp

# Ambiente virtual
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependências
uv pip install -r requirements.txt

# Configurar .env (copiar de .env.example e preencher)
cp .env.example .env

# Testar conexão
uv run python scripts/test_connection.py
```

---

## 🚀 Próximos Milestones

### Curto Prazo (Esta Semana)
- [x] Resolver problema de registrations (98% sucesso) ✅
- [x] Implementar otimização de performance do ETL (50x mais rápido) ✅
- [x] Implementar FastAPI MCP Server (GT-11 a GT-15) ✅
- [x] Traduzir projeto do Linear para documentos locais ✅
- [ ] Completar carga ETL completa de 974k registros com `--full`
- [ ] Validar integridade dos dados no Supabase
- [ ] Gerar relatório de qualidade de dados

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

## 🔄 Workflow de Troca de Ferramenta

**Antes de trocar de Cline → KiloCode/Cursor/etc.:**

1. **Commitar mudanças locais**:
   ```bash
   git add .
   git commit -m "feat: descrição do trabalho realizado"
   ```

2. **Atualizar este documento** (`PROJECT_STATUS.md`):
   - Marcar tarefas concluídas
   - Adicionar novos problemas descobertos
   - Documentar decisões técnicas

3. **Push para GitHub**:
   ```bash
   git push origin main
   ```

4. **Na nova ferramenta**:
   ```bash
   git pull
   # Ler em ordem:
   # 1. docs/PROJECT_STATUS.md (este arquivo)
   # 2. .clinerules
   # 3. docs/ONBOARDING_AGENT.md
   ```

---

## 📚 Documentação Complementar

### Documentos Principais
- **Setup Inicial**: `docs/SETUP.md`
- **Arquitetura**: `docs/DATABASE_REDESIGN_V2.md`
- **ETL V2 Corrections**: `docs/git/CORRECOES_ETL_V2.md`
- **Git Strategies**: `docs/git/branching-strategy.md`, `docs/git/tagging-strategy.md`
- **Onboarding para Agentes**: `docs/ONBOARDING_AGENT.md`

### Documentos Recentes (2026-02-02)
- **Roadmap Completo**: `docs/ROADMAP.md` ⭐ NOVO - Roadmap completo do projeto com 12 épicos
- **Épicos Detalhados**: `docs/EPICS.md` ⭐ NOVO - Detalhes de todos os épicos do Linear
- **Respostas às Perguntas**: `docs/RESPOSTA_PERGUNTAS_INTEGRACOES.md` ⭐ NOVO - Respostas às 3 perguntas sobre integrações
- **Lições Aprendidas**: `docs/LESSONS_LEARNED.md` ⭐ NOVO - Lições aprendidas e melhores práticas
- **Supabase Timeout**: `docs/SUPABASE_TIMEOUT_RECOMMENDATIONS.md` ⭐ NOVO - Recomendações para resolver timeout
- **ETL Optimization**: `docs/ETL_OPTIMIZATION_SUMMARY.md` - Resumo da otimização de ETL
- **ETL Performance Plan**: `docs/ETL_PERFORMANCE_OPTIMIZATION_PLAN.md` - Plano de otimização de performance
- **FastAPI Server Status**: `docs/FASTAPI_MCP_SERVER_STATUS.md` - Status do FastAPI MCP Server
- **MCP Skills Status**: `docs/MCP_SKILLS_STATUS_REPORT.md` - Status de MCP servers e skills
- **Status Reports**: `docs/STATUS_REPORT_2026-02-02.md`, `docs/STATUS_REPORT_2026-02-02_V2.md` - Relatórios de status

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

**Última ação antes desta atualização**: Tradução do projeto do Linear para documentos locais - Criação de docs/ROADMAP.md, docs/EPICS.md e atualização de docs/PROJECT_STATUS.md com o estado atual baseado no Linear. O projeto tem 12 épicos planejados, 3 concluídos (25%), 1 em andamento (8%) e 8 planejados (67%). Os documentos criados servem como "norte" para o desenvolvimento futuro, alinhando o estado do Linear com a documentação local (2026-02-02 18:59 BRT).
