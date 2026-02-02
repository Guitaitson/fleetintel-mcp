# Git Workflow - Política de Commits e Branches

**Data:** 2026-02-02  
**Versão:** 1.0.0  
**Status:** Ativo

---

## 📋 Resumo Executivo

Este documento define a política de commits e branches para o projeto FleetIntel MCP, garantindo consistência, rastreabilidade e flexibilidade no desenvolvimento, independentemente da ferramenta de IA utilizada (Claude Code, Cline, Cursor, KiloCode, etc.).

---

## 🎯 Objetivos

1. **Rastreabilidade:** Histórico claro de todas as mudanças
2. **Flexibilidade:** Facilitar troca entre ferramentas de desenvolvimento
3. **Consistência:** Padrões uniformes para commits e branches
4. **Segurança:** Nunca perder trabalho por falta de commits
5. **Colaboração:** Facilitar revisão e merge de código

---

## 🔄 Política de Commits

### Frequência de Commits

**Regra de Ouro:** **NUNCA deixar arquivos modificados sem commitar por mais de 1 dia**

**Frequência Recomendada:**
- **Commits pequenos e frequentes:** A cada 1-2 horas de trabalho
- **Commits de finalização de tarefa:** Ao completar uma tarefa ou sub-tarefa
- **Commits de correção:** Imediatamente após corrigir um bug
- **Commits de refatoração:** Ao completar uma refatoração significativa

**Quando Commitar:**
- ✅ Ao completar uma funcionalidade
- ✅ Ao corrigir um bug
- ✅ Ao adicionar testes
- ✅ Ao atualizar documentação
- ✅ Ao finalizar o dia de trabalho
- ✅ Antes de trocar de ferramenta de desenvolvimento
- ✅ Antes de fazer experimentos arriscados

**Quando NÃO Commitar:**
- ❌ Código que não compila
- ❌ Código com testes falhando (exceto se for o objetivo)
- ❌ Código incompleto sem contexto
- ❌ Arquivos temporários ou de build

### Conventional Commits

**Formato Padrão:**
```
<tipo>(<escopo>): <descrição curta>

[corpo opcional]

[rodapé opcional]
```

**Tipos de Commit:**

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `feat` | Nova funcionalidade | `feat(api): adicionar endpoint de consulta de veículos` |
| `fix` | Correção de bug | `fix(etl): corrigir erro de parsing de CNPJ` |
| `docs` | Alteração em documentação | `docs(readme): atualizar instruções de instalação` |
| `style` | Alterações de formatação (sem lógica) | `style(app): formatar código com black` |
| `refactor` | Refatoração de código | `refactor(db): otimizar queries de conexão` |
| `perf` | Melhoria de performance | `perf(etl): implementar batch inserts` |
| `test` | Adição ou correção de testes | `test(api): adicionar testes para endpoint de marcas` |
| `chore` | Tarefas de manutenção | `chore(deps): atualizar dependências do Python` |
| `ci` | Alterações em CI/CD | `ci(github): adicionar workflow de testes` |
| `build` | Alterações em build system | `build(docker): otimizar Dockerfile` |

**Escopos Comuns:**

| Escopo | Descrição |
|--------|-----------|
| `api` | API FastAPI |
| `etl` | Scripts ETL |
| `db` | Banco de dados e migrations |
| `docs` | Documentação |
| `tests` | Testes |
| `config` | Configurações |
| `agent` | Agentes LangGraph |
| `mcp` | MCP Servers |

**Exemplos de Commits:**

```bash
# Nova funcionalidade
feat(api): adicionar endpoint de consulta de veículos por placa

# Correção de bug
fix(etl): corrigir erro de parsing de CNPJ com zeros à esquerda

# Documentação
docs(readme): atualizar instruções de instalação com uv

# Refatoração
refactor(db): otimizar queries de conexão com connection pooling

# Performance
perf(etl): implementar batch inserts para reduzir queries de 1.1M para 10k

# Testes
test(api): adicionar testes para endpoint de marcas

# Tarefas de manutenção
chore(deps): atualizar dependências do Python para versões mais recentes
```

**Corpo do Commit (Opcional):**

```bash
feat(api): adicionar endpoint de consulta de veículos por placa

Implementa novo endpoint GET /api/vehicles/{placa} que permite
consultar informações detalhadas de um veículo específico.

O endpoint retorna:
- Informações do veículo (marca, modelo, ano)
- Dados da empresa proprietária
- Informações de registro
- Status de ativação

Closes #123
```

**Rodapé do Commit (Opcional):**

```bash
fix(etl): corrigir erro de parsing de CNPJ com zeros à esquerda

O problema ocorria quando o CNPJ começava com zeros,
pois era tratado como número e os zeros eram removidos.

A solução foi garantir que CNPJs sejam sempre tratados
como strings com padding de zeros (zfill).

Fixes #456
Related to #123
```

---

## 🌿 Política de Branches

### Estrutura de Branches

```
main                    ← Branch principal (produção)
  ├── develop           ← Branch de desenvolvimento
  ├── feature/*         ← Branches de funcionalidades
  ├── bugfix/*          ← Branches de correções
  ├── hotfix/*          ← Branches de correções urgentes
  └── release/*         ← Branches de release
```

### Tipos de Branches

#### 1. `main` (Produção)

**Propósito:** Branch principal, sempre estável e pronto para produção

**Regras:**
- ✅ Sempre estável e testado
- ✅ Tags de versão aplicadas aqui
- ✅ Protegido contra push direto
- ✅ Apenas merges de `develop` ou `release/*`

**Comandos:**
```bash
# Criar tag de versão
git tag -a v1.0.0 -m "Versão 1.0.0 - MVP Release"
git push origin v1.0.0

# Verificar branch atual
git branch --show-current
```

#### 2. `develop` (Desenvolvimento)

**Propósito:** Branch de integração de desenvolvimento

**Regras:**
- ✅ Código integrado de features
- ✅ Testes passando
- ✅ Pode ter funcionalidades em andamento
- ✅ Merge de `feature/*`, `bugfix/*`

**Comandos:**
```bash
# Criar branch develop a partir de main
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop

# Atualizar develop com main
git checkout develop
git merge main
```

#### 3. `feature/*` (Funcionalidades)

**Propósito:** Desenvolvimento de novas funcionalidades

**Regras:**
- ✅ Criado a partir de `develop`
- ✅ Nome descritivo: `feature/gt-11-fastapi-server`
- ✅ Commits frequentes
- ✅ Merge de volta para `develop` via Pull Request

**Comandos:**
```bash
# Criar branch de feature
git checkout develop
git pull origin develop
git checkout -b feature/gt-11-fastapi-server

# Trabalhar na feature
git add .
git commit -m "feat(api): implementar endpoint de consulta de marcas"
git push -u origin feature/gt-11-fastapi-server

# Merge de volta para develop (via Pull Request)
```

**Nomenclatura de Features:**
- `feature/gt-XX-nome-da-feature` - Para GTs do Linear
- `feature/epic-XX-nome-da-feature` - Para épicos do Linear
- `feature/nome-da-feature` - Para features genéricas

#### 4. `bugfix/*` (Correções)

**Propósito:** Correção de bugs não urgentes

**Regras:**
- ✅ Criado a partir de `develop`
- ✅ Nome descritivo: `bugfix/fix-cnpj-parsing`
- ✅ Commits frequentes
- ✅ Merge de volta para `develop` via Pull Request

**Comandos:**
```bash
# Criar branch de bugfix
git checkout develop
git pull origin develop
git checkout -b bugfix/fix-cnpj-parsing

# Corrigir o bug
git add .
git commit -m "fix(etl): corrigir erro de parsing de CNPJ"
git push -u origin bugfix/fix-cnpj-parsing
```

#### 5. `hotfix/*` (Correções Urgentes)

**Propósito:** Correção urgente em produção

**Regras:**
- ✅ Criado a partir de `main`
- ✅ Nome descritivo: `hotfix/critical-security-fix`
- ✅ Merge de volta para `main` E `develop`
- ✅ Criar tag de versão após merge

**Comandos:**
```bash
# Criar branch de hotfix
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# Corrigir o problema
git add .
git commit -m "fix(security): corrigir vulnerabilidade crítica"
git push -u origin hotfix/critical-security-fix

# Merge para main
git checkout main
git merge hotfix/critical-security-fix
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main v1.0.1

# Merge para develop
git checkout develop
git merge hotfix/critical-security-fix
git push origin develop
```

#### 6. `release/*` (Release)

**Propósito:** Preparação de release

**Regras:**
- ✅ Criado a partir de `develop`
- ✅ Nome: `release/v1.0.0`
- ✅ Testes finais
- ✅ Merge para `main` (produção) e `develop`

**Comandos:**
```bash
# Criar branch de release
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# Finalizar release
git checkout main
git merge release/v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main v1.0.0

git checkout develop
git merge release/v1.0.0
git push origin develop
```

---

## 🔄 Workflow de Desenvolvimento

### Fluxo Principal

```
1. Criar branch de feature a partir de develop
   ↓
2. Desenvolver com commits frequentes
   ↓
3. Testar localmente
   ↓
4. Criar Pull Request para develop
   ↓
5. Revisão de código
   ↓
6. Merge em develop
   ↓
7. Criar release quando pronto
   ↓
8. Merge em main e criar tag
```

### Exemplo Prático

```bash
# 1. Atualizar develop
git checkout develop
git pull origin develop

# 2. Criar branch de feature
git checkout -b feature/gt-11-fastapi-server

# 3. Desenvolver com commits frequentes
git add app/main.py
git commit -m "feat(api): criar estrutura básica do FastAPI server"

git add app/config.py
git commit -m "feat(api): adicionar configurações do servidor"

git add app/schemas/query_schemas.py
git commit -m "feat(api): implementar schemas Pydantic para queries"

# 4. Testar localmente
uv run python scripts/test_fastapi_server.py

# 5. Push e criar Pull Request
git push -u origin feature/gt-11-fastapi-server

# 6. Após aprovação, merge em develop (via GitHub UI)

# 7. Atualizar develop
git checkout develop
git pull origin develop

# 8. Deletar branch local e remoto
git branch -d feature/gt-11-fastapi-server
git push origin --delete feature/gt-11-fastapi-server
```

---

## 📝 Checklist de Commit

Antes de fazer um commit, verifique:

### Checklist de Qualidade

- [ ] **Código compila e funciona**
- [ ] **Testes passam** (se aplicável)
- [ ] **Mensagem de commit segue Conventional Commits**
- [ ] **Mensagem é clara e descritiva**
- [ ] **Arquivos corretos estão incluídos**
- [ ] **Arquivos temporários não estão incluídos**
- [ ] **Segredos não estão incluídos** (chaves, tokens, etc.)
- [ ] **Documentação atualizada** (se necessário)

### Checklist de Segurança

- [ ] **Nenhum segredo no commit** (API keys, tokens, senhas)
- [ ] **Arquivos sensíveis no .gitignore**
- [ ] **Variáveis de ambiente no .env.example**
- [ ] **Código não expõe informações sensíveis**

### Checklist de Documentação

- [ ] **README atualizado** (se necessário)
- [ ] **PROJECT_STATUS.md atualizado** (se necessário)
- [ ] **Comentários no código** (se necessário)
- [ ] **Changelog atualizado** (se necessário)

---

## 🔄 Workflow de Troca de Ferramenta

### Antes de Trocar de Ferramenta

1. **Commitar tudo:**
   ```bash
   git add .
   git commit -m "wip: preparando para troca de ferramenta"
   git push
   ```

2. **Atualizar PROJECT_STATUS.md:**
   - Documentar estado atual
   - Listar tarefas em andamento
   - Listar próximos passos

3. **Criar branch de handoff:**
   ```bash
   git checkout -b handoff/2026-02-02-troca-ferramenta
   git push -u origin handoff/2026-02-02-troca-ferramenta
   ```

4. **Documentar contexto:**
   - Criar arquivo `HANDOFF_YYYY-MM-DD.md` em `docs/`
   - Incluir estado do projeto
   - Incluir problemas conhecidos
   - Incluir próximos passos

### Na Nova Ferramenta

1. **Clonar repositório:**
   ```bash
   git clone https://github.com/Guitaitson/fleetintel-mcp.git
   cd fleetintel-mcp
   ```

2. **Ler documentação:**
   - `docs/PROJECT_STATUS.md`
   - `docs/HANDOFF_YYYY-MM-DD.md`
   - `docs/ROADMAP.md`
   - `docs/EPICS.md`

3. **Verificar branch atual:**
   ```bash
   git branch -a
   git checkout <branch-correto>
   ```

4. **Continuar trabalho:**
   - Criar nova feature branch
   - Seguir política de commits
   - Commitar frequentemente

---

## 🏷️ Tags de Versão

### Formato de Versão

**Semantic Versioning (SemVer):**
```
MAJOR.MINOR.PATCH

Exemplos:
- v1.0.0 - MVP Release
- v1.1.0 - Nova funcionalidade
- v1.1.1 - Correção de bug
- v2.0.0 - Mudança breaking
```

**Regras:**
- **MAJOR:** Mudanças incompatíveis com versões anteriores
- **MINOR:** Nova funcionalidade compatível com versões anteriores
- **PATCH:** Correções de bugs compatíveis com versões anteriores

### Criar Tags

```bash
# Criar tag anotada
git tag -a v1.0.0 -m "Versão 1.0.0 - MVP Release

Funcionalidades:
- FastAPI MCP Server implementado
- ETL otimizado com batch inserts
- 6 MCP servers operacionais
- 5 skills instaladas

Correções:
- Pydantic v2 compatibility
- CNPJ parsing com zeros à esquerda
- Connection pooling otimizado"

# Push tag para remoto
git push origin v1.0.0

# Listar tags
git tag -l

# Ver detalhes da tag
git show v1.0.0
```

---

## 🚨 Regras de Ouro

### 1. **NUNCA deixe arquivos modificados sem commitar por mais de 1 dia**
   - Risco de perder trabalho
   - Dificulta colaboração
   - Impossibilita rollback

### 2. **SEMPRE use Conventional Commits**
   - Facilita leitura do histórico
   - Automatiza changelog
   - Padroniza comunicação

### 3. **SEMPRE teste antes de commitar**
   - Código deve compilar
   - Testes devem passar
   - Funcionalidade deve funcionar

### 4. **NUNCA commit segredos**
   - API keys
   - Tokens
   - Senhas
   - Certificados

### 5. **SEMPRE atualize documentação**
   - README.md
   - PROJECT_STATUS.md
   - ROADMAP.md
   - EPICS.md

### 6. **SEMPRE faça commits pequenos e frequentes**
   - 1-2 horas de trabalho por commit
   - Foco em uma tarefa por commit
   - Mensagens claras e descritivas

### 7. **NUNCA faça push direto para main**
   - Use Pull Requests
   - Revisão de código
   - Testes automatizados

### 8. **SEMPRE use branches de feature**
   - Isolamento de desenvolvimento
   - Facilita revisão
   - Permite experimentação

---

## 📚 Referências

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

---

## 📝 Documentos Relacionados

- [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md) - Guia de migração de ferramenta
- [`docs/HANDOFF_CHECKLIST.md`](docs/HANDOFF_CHECKLIST.md) - Checklist de handoff
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Status atual do projeto
- [`docs/ROADMAP.md`](docs/ROADMAP.md) - Roadmap do projeto
- [`docs/EPICS.md`](docs/EPICS.md) - Detalhes dos épicos

---

**Última Atualização:** 2026-02-02  
**Responsável:** Guilherme Taitson  
**Status:** ✅ Ativo
