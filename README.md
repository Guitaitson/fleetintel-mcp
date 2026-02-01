# FleetIntel MCP

MCP Server FastAPI para consulta de dados de frota brasileira.

## Arquitetura

- **mcp_server/**: FastAPI MCP server com endpoints de consulta
- **agent/**: LangGraph agent para processamento inteligente
- **jobs/**: Jobs agendados (sincronização semanal incremental)
- **scripts/**: Utilitários administrativos
- **deploy/**: Configurações Docker e deploy
- **tests/**: Suite de testes
- **docs/**: Documentação técnica

## Stack Técnico

- FastAPI (MCP server)
- LangGraph (agentic workflows)
- Supabase (Postgres gerenciado)
- Redis (cache e filas)
- Docker + Coolify (deployment)

## 🚀 Setup de Desenvolvimento

### Requisitos
- Python 3.11 ou 3.12
- uv (recomendado) ou pip

### ⚙️ Configuração

### 🛠️ Comandos Disponíveis

```bash
make help      # Lista todos os comandos disponíveis
make install   # Instala dependências do projeto
make dev       # Sobe ambiente local (Redis)
make test      # Executa testes
make lint      # Verifica formatação e qualidade do código
make format    # Formata código automaticamente
make logs      # Exibe logs dos serviços
make stop      # Para todos os serviços
```

### Primeiro Setup

```bash
# 1. Instalar dependências
make install

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Subir serviços locais
make dev

# 4. Verificar se está funcionando
make logs
```

### Workflow de Desenvolvimento

```bash
# Antes de commitar código:
make format    # Formata código
make lint      # Verifica qualidade
make test      # Roda testes
```

#### Variáveis de Ambiente

1. Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` com suas credenciais reais

3. Valide a configuração:
   ```bash
   python scripts/validate_env.py
   ```

#### Obtendo Credenciais

**Supabase:**
1. Acesse https://supabase.com/dashboard
2. Crie novo projeto ou selecione existente
3. Em Settings > API, copie:
   - URL
   - anon key
   - service_role key

**OpenAI:**
1. Acesse https://platform.openai.com/api-keys
2. Crie nova API key
3. Copie e guarde com segurança

**Redis:**
- Local: use Docker (veja docker-compose.yml)
- Cloud: https://redis.com/try-free/

**Evolution API:**
Consulte documentação em https://doc.evolution-api.com/

**API de Veículos:**
[Preencher conforme API específica escolhida]

### Instalação com uv (recomendado)
```bash
# Instalar uv se necessário
curl -LsSf https://astral.sh/uv/install.sh | sh

# Criar ambiente virtual e instalar dependências
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

uv pip install -e ".[dev]"
```

### Instalação com pip
```bash
python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

### Atualização de Dependências

**Com uv:**
```bash
uv lock --upgrade
uv pip install -e ".[dev]"
```

**Com pip-tools:**
```bash
pip-compile pyproject.toml --upgrade --output-file=requirements.lock
pip install -r requirements.lock
```

### Ferramentas de Desenvolvimento

**Linting e Formatação:**
```bash
ruff check .
ruff format .
black .
```

**Type Checking:**
```bash
mypy mcp_server/ agent/ jobs/
```

**Testes:**
```bash
pytest                    # Todos os testes
pytest -m unit           # Apenas testes unitários
pytest -m integration    # Apenas testes de integração
pytest --cov             # Com cobertura
```

## 🐳 Ambiente Local (Docker)

### Pré-requisitos
- Docker 20.10+
- Docker Compose 2.0+

### Iniciar Ambiente

```bash
# Opção 1: Usar script helper
./scripts/docker-up.sh

# Opção 2: Comando direto
docker-compose -f docker-compose.local.yml up -d
```

### Serviços Disponíveis

| Serviço | Porta | Descrição |
| :-- | :-- | :-- |
| Redis | 6379 | Cache e filas |
| Redis Commander | 8081 | UI para debug Redis |

### Comandos Úteis

```bash
# Ver status dos serviços
docker-compose -f docker-compose.local.yml ps

# Ver logs
./scripts/docker-logs.sh
./scripts/docker-logs.sh redis  # apenas Redis

# Parar serviços
./scripts/docker-down.sh

# Parar e remover volumes (CUIDADO!)
./scripts/docker-down.sh --volumes

# Reiniciar um serviço específico
docker-compose -f docker-compose.local.yml restart redis

# Acessar console do Redis
docker exec -it fleetintel-redis redis-cli
```

### Troubleshooting

**Porta já em uso:**

```bash
# Verificar o que está usando a porta
lsof -i :6379
# ou
netstat -tlnp | grep 6379
```

**Redis não inicia:**

```bash
# Ver logs detalhados
docker-compose -f docker-compose.local.yml logs redis

# Remover volumes e recriar
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

**Limpar tudo e recomeçar:**

```bash
docker-compose -f docker-compose.local.yml down -v --remove-orphans
docker-compose -f docker-compose.local.yml up -d --force-recreate
```

## Status

🚧 Em desenvolvimento - Epic 1: Bootstrap inicial
