# Migration Guide - Troca de Ferramenta de Desenvolvimento

**Data:** 2026-02-02  
**Versão:** 1.0.0  
**Status:** Ativo

---

## 📋 Resumo Executivo

Este guia fornece instruções detalhadas para migrar entre diferentes ferramentas de desenvolvimento com IA (Claude Code, Cline, Cursor, KiloCode, etc.), garantindo que o contexto do projeto seja preservado e o desenvolvimento continue sem interrupções.

---

## 🎯 Objetivos

1. **Preservação de Contexto:** Manter todo o contexto do projeto durante a migração
2. **Continuidade:** Garantir que o desenvolvimento continue sem interrupções
3. **Consistência:** Manter consistência entre ferramentas
4. **Documentação:** Documentar o processo para futuras migrações
5. **Flexibilidade:** Facilitar trocas frequentes entre ferramentas

---

## 🔄 Processo de Migração

### Fase 1: Preparação (Na Ferramenta Atual)

#### 1.1 Commitar Todo o Trabalho

**Antes de trocar de ferramenta, commitar TUDO:**

```bash
# Verificar status do repositório
git status

# Adicionar todos os arquivos modificados
git add .

# Commitar com mensagem descritiva
git commit -m "wip: preparando para troca de ferramenta

Estado atual:
- FastAPI MCP Server implementado
- ETL otimizado com batch inserts
- 6 MCP servers operacionais
- 5 skills instaladas

Próximos passos:
- Validar dados crus do Excel
- Executar carga completa de 974k registros
- Implementar Epic 4 (API Externa + Job Semanal)"

# Push para remoto
git push
```

#### 1.2 Atualizar Documentação

**Atualizar `docs/PROJECT_STATUS.md`:**

```markdown
## Estado Atual (2026-02-02)

### Última Ação
Preparando para troca de ferramenta de desenvolvimento.

### Componentes Implementados
- [x] MCP Servers (6/6)
- [x] Skills (5/5)
- [x] FastAPI MCP Server
- [x] ETL Otimizado

### Tarefas em Andamento
- [ ] Validar dados crus do arquivo Excel
- [ ] Executar carga completa de 974k registros
- [ ] Implementar Epic 4 (API Externa + Job Semanal)

### Próximos Passos
1. Validar dados crus do Excel
2. Executar carga completa de dados
3. Implementar Epic 4
```

#### 1.3 Criar Branch de Handoff

```bash
# Criar branch de handoff
git checkout -b handoff/2026-02-02-troca-ferramenta

# Push para remoto
git push -u origin handoff/2026-02-02-troca-ferramenta
```

#### 1.4 Criar Documento de Handoff

**Criar `docs/HANDOFF_2026-02-02.md`:**

```markdown
# Handoff - 2026-02-02

**Data:** 2026-02-02  
**Ferramenta Atual:** KiloCode  
**Ferramenta Destino:** [A definir]  
**Branch:** `handoff/2026-02-02-troca-ferramenta`

---

## 📊 Estado do Projeto

### Progresso Geral
- **Épicos Concluídos:** 3 (25%)
- **Épicos Em Andamento:** 1 (8%)
- **Épicos Planejados:** 8 (67%)
- **FASE 0 (Foundation - Data):** 80% concluída

### Componentes Implementados

#### MCP Servers (6/6) ✅
- [x] Memory - Armazenamento de contexto
- [x] N8N - Automação de workflows
- [x] Supabase - Banco de dados PostgreSQL
- [x] Filesystem - Acesso a arquivos
- [x] Linear - Gerenciamento de projetos
- [x] Sequential Thinking - Processamento de pensamento

#### Skills (5/5) ✅
- [x] Changelog Generator
- [x] File Organizer
- [x] LangSmith Fetch
- [x] Lead Research Assistant
- [x] MCP Builder

#### FastAPI MCP Server ✅
- [x] GT-11: Configuração do FastAPI Server
- [x] GT-12: Endpoints de Consulta
- [x] GT-13: Schemas de Dados
- [x] GT-14: Conexão com Banco de Dados
- [x] GT-15: Documentação e Testes

#### ETL Otimizado ✅
- [x] Batch inserts implementados
- [x] Vectorized operations
- [x] Real chunking
- [x] Testado com 100 registros (98 inseridos em 8s)
- [x] Testado com 10.000 registros (9.443 inseridos em 22s)

---

## 📝 Tarefas em Andamento

### PRIORIDADE 3: Carga Completa de Dados
- [ ] Validar dados crus do arquivo Excel estão atualizados
- [ ] Executar carga completa de 974k registros
- [ ] Validar integridade dos dados
- [ ] Gerar relatório de qualidade

### PRIORIDADE 4: Implementar Épicos Futuros
- [ ] Implementar Epic 4 (API Externa + Job Semanal)
- [ ] Implementar Epic 7-12 (Analytics + Lead Scoring)
- [ ] Implementar Epic 8-13 (APIs Enriquecimento)

### PRIORIDADE 5: Documentação de Integrações
- [ ] Criar docs/INTEGRATION_BEST_PRACTICES.md
- [ ] Criar docs/LINEAR_GITHUB_INTEGRATION.md

---

## 🚨 Problemas Conhecidos

### 1. Timeout do Supabase
**Status:** Documentado, não resolvido  
**Documento:** `docs/SUPABASE_TIMEOUT_RECOMMENDATIONS.md`  
**Impacto:** Carga completa de 974k registros não executada

### 2. Dados Crus do Excel
**Status:** Não validado recentemente  
**Ação Necessária:** Validar se dados estão atualizados

---

## 📚 Documentação Essencial

### Documentos de Leitura Obrigatória
1. `docs/PROJECT_STATUS.md` - Status atual do projeto
2. `docs/ROADMAP.md` - Roadmap completo
3. `docs/EPICS.md` - Detalhes dos épicos
4. `docs/GIT_WORKFLOW.md` - Política de commits e branches
5. `docs/ONBOARDING_AGENT.md` - Guia para agentes de IA

### Documentos Técnicos
1. `docs/DATABASE_REDESIGN_V2.md` - Arquitetura do banco
2. `docs/architecture.md` - Arquitetura geral
3. `docs/development.md` - Guia de desenvolvimento
4. `docs/SETUP.md` - Configuração de ambiente

### Documentos de Status
1. `docs/FASTAPI_MCP_SERVER_STATUS.md` - Status do FastAPI
2. `docs/ETL_OPTIMIZATION_SUMMARY.md` - Resumo da otimização
3. `docs/LESSONS_LEARNED.md` - Lições aprendidas
4. `docs/FINAL_STATUS_REPORT_2026-02-02.md` - Relatório final

---

## 🔧 Configuração do Ambiente

### Variáveis de Ambiente
Verificar se `.env` está configurado corretamente:

```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_DB_URL=postgresql://...

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_DEBUG=True

# Outras configurações
LOG_LEVEL=INFO
```

### Dependências
Verificar se dependências estão instaladas:

```bash
# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Verificar dependências
uv pip list

# Instalar dependências se necessário
uv pip install -r requirements.txt
```

---

## 📂 Arquivos Essenciais

### Estrutura do Projeto
```
fleetintel-mcp/
├── app/                    # FastAPI application
├── agent/                  # LangGraph agent code
├── docs/                   # Documentação completa
├── scripts/                # Scripts ETL e utilitários
├── data/                   # Dados (IGNORADO no Git)
├── supabase/migrations/    # Migrations do banco
└── .env                    # Credenciais (IGNORADO no Git)
```

### Arquivos Chave
- `app/main.py` - FastAPI server entry point
- `app/config.py` - Configurações do FastAPI
- `app/schemas/query_schemas.py` - Schemas Pydantic
- `scripts/load_normalized_schema_optimized_v2.py` - ETL otimizado
- `scripts/normalize_data_optimized.py` - Normalização otimizada
- `scripts/load_excel_to_csv_optimized.py` - Excel to CSV otimizado
- `src/config/settings.py` - Configurações do projeto
- `src/fleet_intel_mcp/db/connection.py` - Conexão com banco

---

## 🎯 Próximos Passos Imediatos

### 1. Validar Dados Crus do Excel
```bash
# Verificar arquivo Excel
ls -lh data/raw/*.xlsx

# Verificar data de modificação
stat data/raw/*.xlsx

# Executar script de validação
uv run python scripts/validate_source_files.py
```

### 2. Executar Carga Completa de Dados
```bash
# Executar ETL completo
uv run python scripts/load_excel_to_csv_optimized.py
uv run python scripts/normalize_data_optimized.py
uv run python scripts/load_normalized_schema_optimized_v2.py --full
```

### 3. Validar Integridade dos Dados
```bash
# Verificar contagens no banco
uv run python scripts/check_db_counts.py

# Gerar relatório de qualidade
uv run python scripts/generate_quality_report.py
```

---

## 🔄 Comandos Essenciais

### Git
```bash
# Verificar branch atual
git branch --show-current

# Verificar status
git status

# Verificar commits recentes
git log --oneline -10

# Verificar branches remotos
git branch -a
```

### Testes
```bash
# Testar conexão com Supabase
uv run python scripts/test_connection.py

# Testar FastAPI server
uv run python scripts/test_fastapi_server.py

# Testar ETL com 1 registro
uv run python scripts/test_etl_one_record.py
```

### ETL
```bash
# Excel → CSV Raw
uv run python scripts/load_excel_to_csv_optimized.py

# CSV Raw → CSV Normalized
uv run python scripts/normalize_data_optimized.py

# CSV Normalized → PostgreSQL
uv run python scripts/load_normalized_schema_optimized_v2.py --full
```

---

## 📞 Contato e Suporte

### Responsável
- **Nome:** Guilherme Taitson
- **Email:** [seu email]
- **GitHub:** https://github.com/Guitaitson

### Repositório
- **GitHub:** https://github.com/Guitaitson/fleetintel-mcp
- **Linear:** https://linear.app/gtaitson/project/fleetintel-mcp-bfa0ee37e5f8

---

## ✅ Checklist de Handoff

### Antes de Trocar de Ferramenta
- [x] Todo o trabalho foi commitado
- [x] Documentação atualizada
- [x] Branch de handoff criado
- [x] Documento de handoff criado
- [x] Push para remoto realizado

### Na Nova Ferramenta
- [ ] Repositório clonado
- [ ] Documentação essencial lida
- [ ] Branch correto selecionado
- [ ] Ambiente configurado
- [ ] Dependências instaladas
- [ ] Conexão com banco testada
- [ ] Próximos passos identificados

---

## 📝 Notas Adicionais

### Observações Importantes
1. **Dados Sensíveis:** Nunca commitar `.env` ou dados reais de veículos/empresas
2. **CNPJs/CEPs:** Sempre tratar como strings com padding de zeros
3. **ETL Idempotente:** Re-executar não duplica dados (usa upserts)
4. **Timeout Supabase:** Documentado em `docs/SUPABASE_TIMEOUT_RECOMMENDATIONS.md`

### Lições Aprendidas
1. **Commits Frequentes:** Nunca deixar arquivos modificados sem commitar por mais de 1 dia
2. **Conventional Commits:** Usar formato padrão para mensagens de commit
3. **Documentação:** Manter documentação sempre atualizada
4. **Testes:** Testar localmente antes de commitar

---

**Última Atualização:** 2026-02-02  
**Responsável:** Guilherme Taitson  
**Status:** ✅ Pronto para migração
```

---

### Fase 2: Migração (Na Nova Ferramenta)

#### 2.1 Clonar Repositório

```bash
# Clonar repositório
git clone https://github.com/Guitaitson/fleetintel-mcp.git

# Entrar no diretório
cd fleetintel-mcp

# Verificar branches disponíveis
git branch -a
```

#### 2.2 Selecionar Branch Correto

```bash
# Verificar branch de handoff
git checkout handoff/2026-02-02-troca-ferramenta

# Ou voltar para branch de feature
git checkout feature/gt-9-mvp-guardrails

# Ou voltar para develop
git checkout develop
```

#### 2.3 Ler Documentação Essencial

**Documentos de Leitura Obrigatória:**

1. **`docs/PROJECT_STATUS.md`** - Status atual do projeto
2. **`docs/HANDOFF_YYYY-MM-DD.md`** - Documento de handoff mais recente
3. **`docs/ROADMAP.md`** - Roadmap completo
4. **`docs/EPICS.md`** - Detalhes dos épicos
5. **`docs/GIT_WORKFLOW.md`** - Política de commits e branches
6. **`docs/ONBOARDING_AGENT.md`** - Guia para agentes de IA

**Como Ler:**

```bash
# Ler PROJECT_STATUS.md
cat docs/PROJECT_STATUS.md

# Ler HANDOFF mais recente
ls -lt docs/HANDOFF_*.md | head -1
cat docs/HANDOFF_2026-02-02.md

# Ler ROADMAP
cat docs/ROADMAP.md

# Ler EPICS
cat docs/EPICS.md
```

#### 2.4 Configurar Ambiente

```bash
# Criar ambiente virtual
uv venv

# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
uv pip install -r requirements.txt

# Verificar instalação
uv pip list
```

#### 2.5 Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
nano .env  # Linux/Mac
notepad .env  # Windows
```

**Variáveis Essenciais:**

```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_DB_URL=postgresql://user:password@host:port/database

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_DEBUG=True

# Logging
LOG_LEVEL=INFO
```

#### 2.6 Testar Conexões

```bash
# Testar conexão com Supabase
uv run python scripts/test_connection.py

# Testar FastAPI server
uv run python scripts/test_fastapi_server.py

# Testar ETL com 1 registro
uv run python scripts/test_etl_one_record.py
```

#### 2.7 Continuar Desenvolvimento

```bash
# Criar nova branch de feature
git checkout -b feature/nova-funcionalidade

# Trabalhar na feature
git add .
git commit -m "feat(api): adicionar nova funcionalidade"
git push -u origin feature/nova-funcionalidade
```

---

### Fase 3: Validação (Após Migração)

#### 3.1 Verificar Estado do Projeto

```bash
# Verificar branch atual
git branch --show-current

# Verificar status
git status

# Verificar commits recentes
git log --oneline -10
```

#### 3.2 Validar Componentes

```bash
# Validar MCP servers
# (Depende da ferramenta de IA)

# Validar FastAPI server
uv run python scripts/test_fastapi_server.py

# Validar ETL
uv run python scripts/test_etl_one_record.py

# Validar conexão com banco
uv run python scripts/test_connection.py
```

#### 3.3 Atualizar Documentação

**Atualizar `docs/PROJECT_STATUS.md`:**

```markdown
## Estado Atual (2026-02-02)

### Última Ação
Migrado de [Ferramenta Anterior] para [Nova Ferramenta].

### Componentes Validados
- [x] MCP Servers (6/6)
- [x] Skills (5/5)
- [x] FastAPI MCP Server
- [x] ETL Otimizado
- [x] Conexão com Supabase

### Próximos Passos
1. Validar dados crus do Excel
2. Executar carga completa de 974k registros
3. Implementar Epic 4 (API Externa + Job Semanal)
```

#### 3.4 Commitar Migração

```bash
# Commitar mudanças de migração
git add .
git commit -m "docs: migrar de [Ferramenta Anterior] para [Nova Ferramenta]

- Atualizar PROJECT_STATUS.md
- Validar componentes
- Testar conexões

Próximos passos:
- Validar dados crus do Excel
- Executar carga completa de dados"

# Push para remoto
git push
```

---

## 📚 Arquivos Essenciais para Contexto

### Documentação Obrigatória
1. `docs/PROJECT_STATUS.md` - Status atual do projeto
2. `docs/ROADMAP.md` - Roadmap completo
3. `docs/EPICS.md` - Detalhes dos épicos
4. `docs/GIT_WORKFLOW.md` - Política de commits e branches
5. `docs/ONBOARDING_AGENT.md` - Guia para agentes de IA

### Documentação Técnica
1. `docs/DATABASE_REDESIGN_V2.md` - Arquitetura do banco
2. `docs/architecture.md` - Arquitetura geral
3. `docs/development.md` - Guia de desenvolvimento
4. `docs/SETUP.md` - Configuração de ambiente

### Documentação de Status
1. `docs/FASTAPI_MCP_SERVER_STATUS.md` - Status do FastAPI
2. `docs/ETL_OPTIMIZATION_SUMMARY.md` - Resumo da otimização
3. `docs/LESSONS_LEARNED.md` - Lições aprendidas
4. `docs/FINAL_STATUS_REPORT_2026-02-02.md` - Relatório final

### Código Principal
1. `app/main.py` - FastAPI server entry point
2. `app/config.py` - Configurações do FastAPI
3. `app/schemas/query_schemas.py` - Schemas Pydantic
4. `scripts/load_normalized_schema_optimized_v2.py` - ETL otimizado
5. `scripts/normalize_data_optimized.py` - Normalização otimizada
6. `scripts/load_excel_to_csv_optimized.py` - Excel to CSV otimizado
7. `src/config/settings.py` - Configurações do projeto
8. `src/fleet_intel_mcp/db/connection.py` - Conexão com banco

---

## 🚨 Problemas Comuns e Soluções

### Problema 1: Dependências Não Instaladas

**Sintoma:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solução:**
```bash
# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
uv pip install -r requirements.txt
```

### Problema 2: Variáveis de Ambiente Não Configuradas

**Sintoma:**
```
KeyError: 'SUPABASE_URL'
```

**Solução:**
```bash
# Criar arquivo .env
cp .env.example .env

# Editar .env com suas credenciais
nano .env  # Linux/Mac
notepad .env  # Windows
```

### Problema 3: Branch Errado

**Sintoma:**
```
Arquivos ou funcionalidades não encontrados
```

**Solução:**
```bash
# Verificar branches disponíveis
git branch -a

# Selecionar branch correto
git checkout <branch-correto>
```

### Problema 4: Conexão com Supabase Falha

**Sintoma:**
```
ConnectionError: Could not connect to Supabase
```

**Solução:**
```bash
# Verificar variáveis de ambiente
cat .env | grep SUPABASE

# Testar conexão
uv run python scripts/test_connection.py

# Verificar documentação
cat docs/SUPABASE_SETUP.md
```

---

## 📝 Checklist Completo de Migração

### Antes de Trocar de Ferramenta (Ferramenta Atual)
- [ ] Todo o trabalho foi commitado
- [ ] Documentação atualizada
- [ ] Branch de handoff criado
- [ ] Documento de handoff criado
- [ ] Push para remoto realizado
- [ ] PROJECT_STATUS.md atualizado
- [ ] ROADMAP.md atualizado
- [ ] EPICS.md atualizado

### Na Nova Ferramenta
- [ ] Repositório clonado
- [ ] Branch correto selecionado
- [ ] Documentação essencial lida
  - [ ] PROJECT_STATUS.md
  - [ ] HANDOFF_YYYY-MM-DD.md
  - [ ] ROADMAP.md
  - [ ] EPICS.md
  - [ ] GIT_WORKFLOW.md
  - [ ] ONBOARDING_AGENT.md
- [ ] Ambiente configurado
  - [ ] Ambiente virtual criado
  - [ ] Dependências instaladas
  - [ ] Variáveis de ambiente configuradas
- [ ] Conexões testadas
  - [ ] Conexão com Supabase testada
  - [ ] FastAPI server testado
  - [ ] ETL testado
- [ ] Componentes validados
  - [ ] MCP servers validados
  - [ ] Skills validadas
  - [ ] FastAPI server validado
  - [ ] ETL validado
- [ ] Próximos passos identificados
- [ ] Documentação atualizada
- [ ] Migração commitada

---

## 📚 Referências

- [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md) - Política de commits e branches
- [`docs/HANDOFF_CHECKLIST.md`](docs/HANDOFF_CHECKLIST.md) - Checklist de handoff
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Status atual do projeto
- [`docs/ROADMAP.md`](docs/ROADMAP.md) - Roadmap do projeto
- [`docs/EPICS.md`](docs/EPICS.md) - Detalhes dos épicos
- [`docs/ONBOARDING_AGENT.md`](docs/ONBOARDING_AGENT.md) - Guia para agentes de IA

---

**Última Atualização:** 2026-02-02  
**Responsável:** Guilherme Taitson  
**Status:** ✅ Ativo
