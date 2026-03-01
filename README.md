# FleetIntel MCP

> **Tool MCP especializada em inteligência de frota de veículos pesados do Brasil**

FleetIntel MCP é uma **ferramenta MCP** (Model Context Protocol) que conecta qualquer agente de IA compatível a uma base de dados proprietária de emplacamentos de veículos pesados no Brasil — com dados reais de veículos, empresas proprietárias, localização, preços e histórico de compras.

---

## O que é e o que não é

| ✅ É | ❌ Não é |
|------|----------|
| Uma **tool MCP** que expõe dados de frota | Um agente autônomo |
| Uma API de consulta para **qualquer agente IA** | Um chatbot |
| Um servidor HTTP local exposto via HTTPS | Um SaaS / produto final |
| Uma base de dados **local e offline-first** | Dependente de cloud externa |

---

## Capacidades

Conectado ao FleetIntel MCP, seu agente consegue responder perguntas como:

- *"Quais as 10 empresas que mais compraram veículos pesados no Brasil em 2025?"*
- *"Qual o market share das marcas de caminhão no Rio Grande do Sul em 2024?"*
- *"Quantos veículos a empresa X emplacou nos últimos 3 meses?"*
- *"Liste os emplacamentos de caminhões acima de R$ 500k no Paraná em janeiro/2025."*
- *"Qual a evolução de compras de frota da empresa Y nos últimos 2 anos?"*

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│              AGENTE IA (Claude Desktop / AgentVPS)          │
│  "Quais empresas mais compraram caminhões em 2025?"         │
└────────────────────────┬────────────────────────────────────┘
                         │  MCP Protocol (Streamable HTTP)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CLOUDFLARE TUNNEL (HTTPS)                      │
│              https://mcp.gtaitson.space/mcp                 │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP local
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP SERVER (FastMCP)                           │
│              localhost:8888 · Uvicorn · Streamable HTTP     │
│                                                             │
│   Tools disponíveis:                                        │
│   • search_vehicles          • search_empresas              │
│   • search_registrations     • get_stats                    │
│   • top_empresas_by_registrations                           │
│   • count_empresa_registrations                             │
│   • get_market_share                                        │
└────────────────────────┬────────────────────────────────────┘
                         │  SQLAlchemy / asyncpg
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL 16 (Docker local)                   │
│              ~986.000 veículos · ~170.000 empresas          │
│              ~1.000.000+ emplacamentos                      │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │  Sync incremental diário
                         │
┌─────────────────────────────────────────────────────────────┐
│              SCRIPT DE SYNC (scripts/sync_from_api.py)      │
│              Busca novos emplacamentos via API externa       │
│              Roda diariamente · upsert por chassi/CNPJ       │
└─────────────────────────────────────────────────────────────┘
```

---

## Stack Técnico

| Componente | Tecnologia | Versão |
|-----------|------------|--------|
| MCP Server | FastMCP (streamable-http) | ≥ 1.0 |
| Runtime | Uvicorn + asyncio | ≥ 0.32 |
| Banco de dados | PostgreSQL 16 Alpine | Docker |
| Cache | Redis 7 Alpine | Docker |
| Túnel HTTPS | Cloudflare Tunnel (cloudflared) | v2025+ |
| ETL / Sync | Python + httpx + asyncpg | ≥ 3.11 |
| Containerização | Docker Compose | local dev |

---

## MCP Tools

| Tool | Descrição |
|------|-----------|
| `search_vehicles` | Busca veículos por chassi, placa, marca, modelo ou faixa de ano |
| `search_empresas` | Busca empresas por CNPJ, razão social, nome fantasia ou segmento |
| `search_registrations` | Busca emplacamentos por período, UF, município, preço ou veículo |
| `get_stats` | Contagem geral: marcas, modelos, veículos, empresas, emplacamentos |
| `top_empresas_by_registrations` | Top N empresas por volume de compras em um ano (com filtro por UF) |
| `count_empresa_registrations` | Conta emplacamentos de uma empresa específica por nome e ano |
| `get_market_share` | Market share de marcas por número de emplacamentos em um ano |

---

## Setup Rápido

### Pré-requisitos

- Python 3.11 ou 3.12
- Docker + Docker Compose
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) (para exposição HTTPS)
- uv (recomendado) ou pip

### 1. Clonar e instalar dependências

```bash
git clone https://github.com/SEU_USUARIO/fleetintel-mcp.git
cd fleetintel-mcp

# Criar ambiente virtual e instalar
uv venv && source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\Activate.ps1          # Windows

uv pip install -e "."
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais:
# DATABASE_URL, REDIS_URL, MCP_AUTH_TOKEN, HUBQUEST_API_KEY
```

### 3. Subir banco de dados

```bash
docker compose -f docker-compose.local.yml up -d
```

### 4. Iniciar o MCP Server

```bash
python -m mcp_server.main
# [FleetIntel MCP] Iniciando em modo streamable-http na porta 8888
# INFO: Uvicorn running on http://0.0.0.0:8888
```

### 5. (Opcional) Expor via Cloudflare Tunnel

```bash
cloudflared tunnel --config infra/cloudflare-tunnel.yml run
```

### 6. Testar localmente

```bash
# Deve retornar HTTP 404 em / e funcionar em /mcp
curl -s http://localhost:8888/
```

> Para o guia completo com exemplos de uso no Claude Desktop e AgentVPS, veja [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md).

---

## Sincronização de Dados

Os dados são atualizados via script incremental que consome a API externa de emplacamentos:

```bash
# Sync incremental (últimos 7 dias — uso diário recomendado)
python scripts/sync_from_api.py --mode incremental

# Sync completo histórico (uso único na carga inicial)
python scripts/sync_from_api.py --mode full --date-range 90

# Verificar estado do banco
python scripts/db_health.py
```

> Documentação completa da lógica de sync: [docs/DATA_SYNC.md](docs/DATA_SYNC.md)

---

## Dados no Banco

| Tabela | Descrição | Volume estimado |
|--------|-----------|-----------------|
| `vehicles` | Veículos com chassi, placa, marca, modelo, ano | ~986k |
| `empresas` | Proprietários com CNPJ, razão social, endereço, contatos | ~170k |
| `registrations` | Emplacamentos com data, UF, município, preço | ~1M+ |
| `marcas` | Lookup de fabricantes | ~30 |
| `modelos` | Lookup de modelos por marca | ~800 |
| `enderecos` | Endereços das empresas | ~170k |
| `contatos` | Telefones e emails das empresas | ~170k |
| `sync_logs` | Histórico de execuções de sync | - |

---

## Estrutura de Diretórios

```
fleetintel-mcp/
├── mcp_server/
│   └── main.py             # MCP Server com todas as tools
├── scripts/
│   ├── sync_from_api.py    # Rotina de sync incremental via API
│   ├── setup_database.sql  # Schema inicial do PostgreSQL
│   ├── db_health.py        # Verificação de saúde do banco
│   └── ...                 # Outros utilitários
├── src/fleet_intel_mcp/
│   ├── config.py           # Settings (pydantic-settings)
│   └── db/connection.py    # Pool de conexão async
├── infra/
│   └── cloudflare-tunnel.yml  # Configuração do túnel HTTPS
├── docker-compose.local.yml   # PostgreSQL + Redis locais
├── docs/
│   ├── ARCHITECTURE.md     # Arquitetura detalhada
│   ├── QUICKSTART.md       # Setup passo a passo
│   ├── USAGE_GUIDE.md      # Guia de uso com exemplos
│   └── DATA_SYNC.md        # Documentação do sync de dados
└── .env.example            # Template de variáveis de ambiente
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | ✅ | Redis URL (`redis://localhost:6379/1`) |
| `MCP_AUTH_TOKEN` | Recomendado | Bearer token para autenticação do MCP Server |
| `MCP_PORT` | Não | Porta do servidor (padrão: `8888`) |
| `HUBQUEST_API_KEY` | Para sync | Chave da API de dados de emplacamentos |
| `HUBQUEST_API_URL` | Para sync | URL da API (padrão: configurado no script) |
| `FLEETINTEL_DB_PASSWORD` | Docker | Senha do PostgreSQL no Docker Compose |

---

## Endpoints MCP

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/mcp` | Endpoint principal MCP (Streamable HTTP) |

**Autenticação:**
```
Authorization: Bearer <MCP_AUTH_TOKEN>
Content-Type: application/json
Accept: application/json, text/event-stream
```

---

## Licença

MIT — Guilherme Taitson
