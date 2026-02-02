
**Bem-vindo(a) ao FleetIntel MCP!** 🚀

Este documento é um guia de onboarding rápido para agentes de IA (Cline, KiloCode, Cursor, Windsurf, etc.) que vão trabalhar neste projeto.

---

## 🎯 Leia Isto Primeiro (Ordem de Prioridade)

Se você é um agente de IA recém-chegado ao projeto, leia nesta ordem:

1. **Este arquivo** (`docs/ONBOARDING_AGENT.md`) — Você está aqui! ✅
2. **`docs/PROJECT_STATUS.md`** — Estado atual do projeto, problemas em aberto, próximos passos
3. **`.clinerules`** (na raiz) — Contexto técnico, stack, convenções de código
4. **`docs/DATABASE_REDESIGN_V2.md`** — Arquitetura do banco de dados
5. **`docs/git/CORRECOES_ETL_V2.md`** — Correções recentes no ETL (importante!)
6. **`README.md`** — Overview geral do projeto

---

## 🏗️ Estrutura do Projeto (Quick Reference)

```
fleetintel-mcp/
├── .clinerules              # ⭐ Contexto para agentes de IA
├── .env                     # 🔒 Credenciais (NUNCA commitado)
├── docs/
│   ├── PROJECT_STATUS.md    # ⭐ Estado atual do projeto
│   ├── ONBOARDING_AGENT.md  # ⭐ Este arquivo
│   ├── DATABASE_REDESIGN_V2.md
│   └── git/
│       ├── CORRECOES_ETL_V2.md
│       └── tagging-strategy.md
├── scripts/                 # Scripts ETL e utilitários
│   ├── load_excel_to_csv.py
│   ├── normalize_data.py
│   └── load_normalized_schema.py
├── data/                    # 🔒 Dados locais (NUNCA commitado)
│   ├── raw/                 # Excel/CSV originais
│   └── processed/           # CSVs normalizados
├── supabase/migrations/     # Migrations do banco
└── app/                     # FastAPI application (futuro)
```

---

## ⚡ Setup Rápido (First Time)

Se você está configurando o projeto pela primeira vez:

```bash
# 1. Clone o projeto
git clone git@github.com:Guitaitson/fleetintel-mcp.git
cd fleetintel-mcp

# 2. Criar ambiente virtual Python
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependências
uv pip install -r requirements.txt

# 4. Configurar .env (copiar de .env.example e preencher com credenciais)
cp .env.example .env
# Editar .env com suas credenciais Supabase

# 5. Testar conexão com Supabase
uv run python scripts/test_connection.py
```

---

## 🔄 Workflow de Continuação (Switching Tools)

Se você está continuando um trabalho de outro agente:

```bash
# 1. Pull das últimas mudanças
git pull origin main

# 2. Ler documentação de estado
# Leia em ordem:
# - docs/PROJECT_STATUS.md
# - .clinerules
# - Este arquivo (você já leu!)

# 3. Verificar ambiente ativo
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 4. Continuar de onde parou
# Veja "Próximos Passos" em PROJECT_STATUS.md
```

---

## 📋 Estado Atual (As of 2026-01-31)

### ✅ O que está funcionando
- Database schema normalizado (PostgreSQL 17.6 + Supabase)
- ETL Pipeline parcialmente funcional:
  - ✅ Excel → CSV Raw (974k registros)
  - ✅ CSV Raw → CSV Normalized (974k registros)
  - ⚠️ CSV Normalized → Database (marcas, modelos, vehicles, empresas OK; registrations FALHA)

### 🔴 Problema Crítico em Aberto
**Registrations com 0 inserções** (100% erro no teste de 100 registros)

**Localização**: `scripts/load_normalized_schema.py`, função `load_registrations()`

**Sintoma**: Vehicles e empresas são criados corretamente, mas as registrations (junction table) não são inseridas.

**Hipótese**: Os maps (`vehicle_map`, `empresa_map`) não fazem match com os dados das rows. Possível problema de tipos ou formatação de chaves (chassi, CNPJ).

**Próxima Ação**: Adicionar debug logging para identificar por que os lookups falham.

---

## 🚨 Regras de Negócio Críticas

**ATENÇÃO**: Estas regras são ESSENCIAIS e causaram bugs no passado:

1. **CNPJs, CPFs, CEPs, CNAEs são SEMPRE strings com padding de zeros**
   - CNPJ: 14 dígitos → `str(cnpj).zfill(14)`
   - CPF: 11 dígitos → `str(cpf).zfill(11)`
   - CEP: 8 dígitos → `str(cep).zfill(8)`
   - CNAE: 7 dígitos → `str(cnae).zfill(7)`

2. **Pandas lê esses códigos como floats por padrão** (BUG!)
   - Sempre usar `dtype=str` ao ler Excel/CSV
   - Sempre forçar `.astype('object')` antes de salvar

3. **Dados sensíveis NUNCA vão para Git**
   - `.env` com credenciais
   - `data/` com PII
   - CSVs/Excel com dados reais

---

## 🛠️ Comandos Essenciais

### ETL Pipeline
```bash
# Passo 1: Excel → CSV Raw
uv run python scripts/load_excel_to_csv.py

# Passo 2: CSV Raw → CSV Normalized
uv run python scripts/normalize_data.py

# Passo 3: CSV Normalized → PostgreSQL (teste 100 registros)
uv run python scripts/load_normalized_schema.py

# Passo 3 (carga completa - APÓS TESTES PASSAREM)
uv run python scripts/load_normalized_schema.py --full
```

### Testes
```bash
# Testar conexão Supabase
uv run python scripts/test_connection.py

# Testar ETL com 1 registro
uv run python scripts/test_etl_one_record.py
```

### Database
```bash
# Aplicar migrations
uv run python scripts/apply_migrations.py

# Verificar schema
uv run python scripts/check_schema.py
```

---

## 🔐 Segurança e Git

### O que NUNCA vai para o Git
- `.env` (credenciais)
- `data/raw/` (dados brutos)
- `data/processed/` (dados normalizados)
- `*.csv`, `*.xlsx`, `*.xls` (arquivos de dados)

### O que VAI para o Git
- Código (scripts, app, migrations)
- Documentação (docs/)
- Configurações (`.env.example`, não `.env`)
- `.clinerules` e outros metadados de projeto

---

## 📚 Documentação Detalhada

Para entender mais sobre cada área:

- **Setup Inicial**: `docs/SETUP.md`
- **Arquitetura do Banco**: `docs/DATABASE_REDESIGN_V2.md`
- **Correções ETL V2**: `docs/git/CORRECOES_ETL_V2.md`
- **Estratégia Git**: `docs/git/branching-strategy.md`, `docs/git/tagging-strategy.md`
- **Status Completo**: `docs/PROJECT_STATUS.md`

---

## 🤖 Dicas para Agentes de IA

### Ao começar uma nova tarefa:
1. Leia `PROJECT_STATUS.md` para saber o que já foi feito
2. Verifique os "Próximos Passos" na documentação
3. Sempre teste localmente antes de commitar
4. Atualize `PROJECT_STATUS.md` ao concluir tarefas

### Ao trocar de ferramenta:
1. Commite TODAS as mudanças locais
2. Atualize `PROJECT_STATUS.md` com o progresso
3. Push para GitHub
4. Na nova ferramenta: pull + ler `PROJECT_STATUS.md` novamente

### Ao resolver bugs:
1. Documente o bug em `PROJECT_STATUS.md` (seção "Problemas em Aberto")
2. Documente a solução em `PROJECT_STATUS.md` (seção "Decisões Técnicas")
3. Se for um bug de arquitetura, considere criar um doc em `docs/git/`

---

## 🎓 Conceitos-Chave do Projeto

### Stack
- **Backend**: Python 3.12+ com FastAPI
- **Database**: PostgreSQL 17.6 (Supabase)
- **ORM**: AsyncPG + SQLAlchemy (async)
- **ETL**: Pandas
- **Agent**: LangGraph (futuro)

### Schema do Banco (Simplificado)
```
marcas (id, nome)
  ↓
modelos (id, marca_id, nome, ano)
  ↓
vehicles (id, modelo_id, chassi, placa)

empresas (id, cpf_cnpj, razao_social)
  ↓
enderecos (id, empresa_id, cep, logradouro)
contatos (id, empresa_id, telefone, email)

registrations (vehicle_id, empresa_id, data_emplacamento)
  ↑ Junction table entre vehicles e empresas
```

---

## ✅ Checklist de Onboarding Completo

Você completou o onboarding quando:

- [ ] Leu este documento inteiro
- [ ] Leu `PROJECT_STATUS.md`
- [ ] Leu `.clinerules`
- [ ] Configurou `.env` com credenciais
- [ ] Instalou dependências (`uv pip install -r requirements.txt`)
- [ ] Testou conexão com Supabase (`uv run python scripts/test_connection.py`)
- [ ] Entendeu o problema crítico atual (registrations com 0 inserções)
- [ ] Sabe onde encontrar documentação detalhada

---

**Pronto!** Agora você está preparado(a) para trabalhar no FleetIntel MCP. 🚀

Se tiver dúvidas, consulte `PROJECT_STATUS.md` ou os documentos específicos em `docs/`.

---

**Última atualização**: 2026-01-31 12:33 BRT