# FleetIntel MCP - Status do Projeto

**Última Atualização**: 2026-01-31 12:32 BRT  
**Branch Atual**: main  
**Último Commit**: 04f6ed9994b7a10a4a30eb49b5889fdb961c45bc

---

## 🎯 Visão Geral

Este documento reflete o **estado atual** do projeto FleetIntel MCP. É atualizado antes de cada troca de ferramenta de agente (Cline, KiloCode, Cursor, etc.) ou antes de commits importantes.

---

## 📊 Status dos Epics

### ✅ Epic 0-3: Setup + Database Redesign + ETL V1
**Status**: CONCLUÍDO  
**Documentação**: `docs/EPIC_0-3_FINAL_STATUS.md`

- Database redesign V2 implementado
- Migrations aplicadas
- Schema normalizado funcional

### ⚠️ Epic 4: ETL V2 - Correções de Tipos de Dados
**Status**: EM ANDAMENTO (95%)  
**Documentação**: `docs/git/CORRECOES_ETL_V2.md`

**Progresso**:
- ✅ Identificado problema: CNPJs, CEPs, CNAEs sendo lidos como floats
- ✅ Corrigido `scripts/load_excel_to_csv.py` (DTYPE_MAP)
- ✅ Corrigido `scripts/normalize_data.py` (zfill e forcing string types)
- ✅ Corrigido `scripts/load_normalized_schema.py` (dtype=str no CSV read)
- ✅ Excel → CSV Raw executado: **974,122 registros**
- ✅ CSV Raw → CSV Normalized executado: **974,122 registros**
- ❌ **Teste com 100 registros: 0 registrations inseridos** (100% erro)

**Problema Crítico em Aberto**:
```
Teste load_normalized_schema.py (100 registros):
- Marcas: 6 inseridos ✅
- Modelos: 30 inseridos ✅
- Vehicles: 100 inseridos ✅
- Empresas: 50 inseridos ✅
- Registrations: 0 inseridos ❌ (100 errors)
```

**Hipótese**: Os maps (`vehicle_map`, `empresa_map`) não estão fazendo match com os dados dos registros. Possíveis causas:
- Keys dos maps (chassi, CNPJ) podem ter formato diferente dos valores nas rows
- Possível problema de None/NaN handling
- Possível incompatibilidade de tipos (string vs float residual)

**Próximos Passos Técnicos**:
1. Adicionar debug logging em `load_registrations()`:
   ```python
   vehicle_id = vehicle_map.get(row['chassi'])
   if not vehicle_id:
       print(f"❌ Vehicle not found for chassi: {row['chassi']}")
   
   cnpj_key = row['cpf_cnpj_proprietario']
   empresa_id = empresa_map.get(cnpj_key)
   if not empresa_id:
       print(f"❌ Empresa not found for CNPJ: {cnpj_key}")
   ```
2. Verificar tipos de dados entre map keys e row values
3. Testar com sample pequeno (5-10 registros) com logging verboso
4. Corrigir matching issue
5. Re-testar com 100 registros
6. Se passar, executar carga completa (974k registros)

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

### 🔴 CRÍTICO: Registrations com 0 inserções
- **Onde**: `scripts/load_normalized_schema.py`
- **Sintoma**: 100% das registrations falham ao inserir
- **Impacto**: Carga completa de 974k registros bloqueada
- **Investigação**: Ver seção "Epic 4" acima

### 🟡 MÉDIO: Dados CSV grandes não protegidos inicialmente
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
- [ ] Resolver problema de registrations (0 inserções)
- [ ] Completar carga ETL de 974k registros
- [ ] Validar integridade dos dados no Supabase

### Médio Prazo (Próximas 2 Semanas)
- [ ] Implementar FastAPI MCP Server (GT-11 a GT-15)
- [ ] Criar endpoints básicos de consulta
- [ ] Configurar CI/CD básico

### Longo Prazo (Próximo Mês)
- [ ] Implementar agente LangGraph (GT-16 a GT-20)
- [ ] Preparar integração WhatsApp (GT-21 a GT-25)
- [ ] Refinar documentação de API

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

- **Setup Inicial**: `docs/SETUP.md`
- **Arquitetura**: `docs/DATABASE_REDESIGN_V2.md`
- **ETL V2 Corrections**: `docs/git/CORRECOES_ETL_V2.md`
- **Git Strategies**: `docs/git/branching-strategy.md`, `docs/git/tagging-strategy.md`
- **Onboarding para Agentes**: `docs/ONBOARDING_AGENT.md`

---

## 🤝 Contribuindo

Este projeto usa:
- **Conventional Commits** (feat:, fix:, docs:, etc.)
- **Branches**: feature/, bugfix/, hotfix/ + descrição
- **PRs**: Obrigatório para mudanças não triviais

---

**Última ação antes desta atualização**: Criação de `.clinerules` e atualização de `.gitignore` para proteger dados sensíveis (2026-01-31 12:32 BRT).