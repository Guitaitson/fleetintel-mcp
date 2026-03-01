# FleetIntel MCP — Arquitetura e Engenharia

> Documento de referência técnica para engenheiros, integradores e agentes de IA que desejam entender como o sistema funciona internamente.

---

## 1. Visão Geral

O FleetIntel MCP é um **servidor MCP especializado** que expõe uma base de dados proprietária de emplacamentos de veículos pesados do Brasil (caminhões, ônibus, implementos) para qualquer agente de IA compatível com o protocolo MCP.

**Decisão de design central**: o servidor é *stateless* e *read-only* para os agentes. Toda escrita de dados acontece via rotina de sync separada, completamente desacoplada do servidor MCP.

---

## 2. Diagrama de Arquitetura

```
  ┌─────────────────────────────────────────────────────────┐
  │   CAMADA DE CONSUMO (qualquer agente MCP-compatível)    │
  │                                                         │
  │   Claude Desktop  │  AgentVPS  │  n8n  │  API clients  │
  └────────────────────────┬────────────────────────────────┘
                           │  HTTPS · Bearer token auth
                           │  Content-Type: application/json
                           │  Accept: application/json, text/event-stream
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │   CLOUDFLARE TUNNEL (edge público)                      │
  │   https://mcp.gtaitson.space/mcp                        │
  │   Edge nodes: gru10, gru18, gru13, gru02 (São Paulo)   │
  └────────────────────────┬────────────────────────────────┘
                           │  HTTP local · localhost:8888
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │   MCP SERVER (FastMCP · Uvicorn · Streamable HTTP)      │
  │   localhost:8888 · host=0.0.0.0                         │
  │                                                         │
  │   7 tools disponíveis:                                  │
  │   ├── search_vehicles                                   │
  │   ├── search_empresas                                   │
  │   ├── search_registrations                              │
  │   ├── get_stats                                         │
  │   ├── top_empresas_by_registrations                     │
  │   ├── count_empresa_registrations                       │
  │   └── get_market_share                                  │
  └────────────────────────┬───────────────────┬────────────┘
                           │ asyncpg           │ redis-py
                           ▼                   ▼
  ┌────────────────────┐  ┌────────────────────────────────┐
  │  PostgreSQL 16     │  │  Redis 7                       │
  │  Docker local      │  │  Docker local                  │
  │  :5432             │  │  :6379                         │
  │  ~986k veículos    │  │  Cache de consultas frequentes │
  │  ~170k empresas    │  │  TTL configurável por tool     │
  │  ~1M emplacamentos │  └────────────────────────────────┘
  └────────┬───────────┘
           ▲  upsert incremental
           │
  ┌────────┴───────────────────────────────────────────────┐
  │  SYNC SCRIPT (scripts/sync_from_api.py)                │
  │  Roda diariamente via Task Agendada ou cron            │
  │  Consome API externa · Paginação · Retry · Warm-up     │
  └────────────────────────────────────────────────────────┘
```

---

## 3. Stack Técnico

| Camada | Tecnologia | Versão | Justificativa |
|--------|-----------|--------|---------------|
| MCP Protocol | FastMCP (streamable-http) | ≥ 1.0 | Suporta HTTP stateless, SSE e streaming |
| Runtime | Uvicorn + asyncio | ≥ 0.32 | ASGI async de alta performance |
| Banco de dados | PostgreSQL 16 Alpine | Docker | Confiabilidade, sem custo de cloud |
| Pool de conexões | asyncpg + SQLAlchemy 2.x | ≥ 0.30 / ≥ 2.0 | Pool async com reconexão automática |
| Cache | Redis 7 Alpine | Docker | Evita re-query para perguntas frequentes |
| Túnel HTTPS | Cloudflare Tunnel | v2025+ | URL estável sem IP fixo, TLS automático |
| ETL / Sync | Python + httpx | ≥ 3.11 / ≥ 0.28 | Sync incremental com retry e paginação |
| Config | pydantic-settings | ≥ 2.6 | Validação de env vars com tipos |

---

## 4. Schema do Banco de Dados

### 4.1 Tabelas de Lookup

```sql
CREATE TABLE IF NOT EXISTS marcas (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modelos (
    id          SERIAL PRIMARY KEY,
    marca_id    INTEGER NOT NULL REFERENCES marcas(id),
    nome        VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(marca_id, nome)
);
```

### 4.2 Veículos

```sql
CREATE TABLE IF NOT EXISTS vehicles (
    id              SERIAL PRIMARY KEY,
    chassi          VARCHAR(50) UNIQUE NOT NULL,
    placa           VARCHAR(10),
    marca_id        INTEGER REFERENCES marcas(id),
    modelo_id       INTEGER REFERENCES modelos(id),
    ano_fabricacao  SMALLINT,
    ano_modelo      SMALLINT,
    combustivel     VARCHAR(50),
    potencia        NUMERIC(10,2),
    subsegmento     VARCHAR(100),
    segmento        VARCHAR(100),
    concessionario  VARCHAR(200),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 Empresas

```sql
CREATE TABLE IF NOT EXISTS empresas (
    id                  SERIAL PRIMARY KEY,
    cnpj                VARCHAR(20) UNIQUE NOT NULL,
    razao_social        VARCHAR(300),
    nome_fantasia       VARCHAR(300),
    cnae_principal      VARCHAR(10),
    segmento_cliente    VARCHAR(200),
    data_abertura       DATE,
    porte               VARCHAR(50),
    natureza_juridica   VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enderecos (
    id          SERIAL PRIMARY KEY,
    empresa_id  INTEGER UNIQUE NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    logradouro  VARCHAR(300),
    numero      VARCHAR(20),
    complemento VARCHAR(100),
    bairro      VARCHAR(100),
    municipio   VARCHAR(100),
    uf          CHAR(2),
    cep         VARCHAR(10),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contatos (
    id          SERIAL PRIMARY KEY,
    empresa_id  INTEGER UNIQUE NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    telefone1   VARCHAR(30),
    telefone2   VARCHAR(30),
    email1      VARCHAR(200),
    email2      VARCHAR(200),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.4 Emplacamentos

```sql
CREATE TABLE IF NOT EXISTS registrations (
    id                  SERIAL PRIMARY KEY,
    vehicle_id          INTEGER NOT NULL REFERENCES vehicles(id),
    empresa_id          INTEGER REFERENCES empresas(id),
    data_emplacamento   DATE NOT NULL,
    municipio           VARCHAR(100),
    uf                  CHAR(2),
    preco               NUMERIC(15,2),
    preco_validado      BOOLEAN DEFAULT FALSE,
    data_atualizacao    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(vehicle_id, data_emplacamento)
);
```

### 4.5 Controle de Sync

```sql
CREATE TABLE IF NOT EXISTS sync_logs (
    id               SERIAL PRIMARY KEY,
    mode             VARCHAR(20) NOT NULL,
    date_type        VARCHAR(20) NOT NULL,
    date_range       VARCHAR(50),
    started_at       TIMESTAMPTZ NOT NULL,
    finished_at      TIMESTAMPTZ,
    status           VARCHAR(20) DEFAULT 'running',
    records_fetched  INTEGER DEFAULT 0,
    records_upserted INTEGER DEFAULT 0,
    records_failed   INTEGER DEFAULT 0,
    pages_fetched    INTEGER DEFAULT 0,
    error_message    TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.6 Índices de Performance

```sql
-- Veículos
CREATE INDEX IF NOT EXISTS idx_vehicles_chassi     ON vehicles(chassi);
CREATE INDEX IF NOT EXISTS idx_vehicles_placa       ON vehicles(placa);
CREATE INDEX IF NOT EXISTS idx_vehicles_marca_id    ON vehicles(marca_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_modelo_id   ON vehicles(modelo_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_segmento    ON vehicles(segmento);

-- Empresas
CREATE INDEX IF NOT EXISTS idx_empresas_cnpj        ON empresas(cnpj);
CREATE INDEX IF NOT EXISTS idx_empresas_razao       ON empresas(razao_social);
CREATE INDEX IF NOT EXISTS idx_empresas_segmento    ON empresas(segmento_cliente);

-- Emplacamentos
CREATE INDEX IF NOT EXISTS idx_reg_empresa_id       ON registrations(empresa_id);
CREATE INDEX IF NOT EXISTS idx_reg_vehicle_id       ON registrations(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_reg_data             ON registrations(data_emplacamento);
CREATE INDEX IF NOT EXISTS idx_reg_uf               ON registrations(uf);
CREATE INDEX IF NOT EXISTS idx_reg_municipio        ON registrations(municipio);
CREATE INDEX IF NOT EXISTS idx_reg_data_empresa     ON registrations(data_emplacamento, empresa_id);

-- Endereços / Contatos
CREATE INDEX IF NOT EXISTS idx_enderecos_uf         ON enderecos(uf);
CREATE INDEX IF NOT EXISTS idx_enderecos_municipio  ON enderecos(municipio);
```

---

## 5. Protocolo MCP — Fluxo Detalhado

O MCP (Model Context Protocol) da Anthropic define como agentes de IA se comunicam com servidores de ferramentas. O FleetIntel MCP usa o transport **Streamable HTTP**.

### 5.1 Fluxo de Uma Chamada de Tool

```
Agente (Claude Desktop / AgentVPS)
  │
  │  POST https://mcp.gtaitson.space/mcp
  │  Headers:
  │    Authorization: Bearer <MCP_AUTH_TOKEN>
  │    Content-Type: application/json
  │    Accept: application/json, text/event-stream
  │  Body: { "method": "tools/call", "params": { "name": "get_stats", "arguments": {} } }
  │
  ▼
Cloudflare Edge (São Paulo)
  │  QUIC/HTTP2 · TLS 1.3 · Cache bypass para /mcp
  ▼
MCP Server (FastMCP · Uvicorn)
  │  Valida Bearer token
  │  Roteia para handler da tool
  │  Executa query async via asyncpg
  │  Retorna JSON estruturado
  ▼
Resposta SSE / JSON
  │  { "result": { "content": [{ "type": "text", "text": "..." }] } }
  ▼
Agente processa e formula resposta ao usuário
```

### 5.2 Autenticação

O servidor valida o header `Authorization: Bearer <token>` comparando com a variável `MCP_AUTH_TOKEN`. Requisições sem token ou com token inválido recebem `401 Unauthorized`.

### 5.3 Endpoint

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/mcp` | Endpoint principal MCP |
| `GET`  | `/`   | Retorna 404 (intencional) |

---

## 6. MCP Tools — Referência Completa

### `search_vehicles`
Busca veículos por múltiplos critérios.

**Parâmetros:**
- `chassi` (str, opcional) — busca exata
- `placa` (str, opcional) — busca exata
- `marca` (str, opcional) — ILIKE `%termo%`
- `modelo` (str, opcional) — ILIKE `%termo%`
- `ano_min` / `ano_max` (int, opcional) — faixa de ano fabricação
- `segmento` (str, opcional) — caminhao, onibus, implemento, etc.
- `limit` (int, padrão 20, máx 100)

---

### `search_empresas`
Busca empresas proprietárias de veículos pesados.

**Parâmetros:**
- `cnpj` (str, opcional) — busca exata
- `razao_social` (str, opcional) — ILIKE `%termo%`
- `nome_fantasia` (str, opcional) — ILIKE `%termo%`
- `segmento` (str, opcional) — segmento_cliente
- `uf` (str, opcional) — filtro por estado via endereços
- `limit` (int, padrão 20)

---

### `search_registrations`
Busca emplacamentos com filtros combinados.

**Parâmetros:**
- `data_inicio` / `data_fim` (str `YYYY-MM-DD`, opcional)
- `uf` (str, opcional)
- `municipio` (str, opcional) — ILIKE
- `preco_min` / `preco_max` (float, opcional)
- `marca` (str, opcional)
- `empresa_cnpj` (str, opcional)
- `limit` (int, padrão 50, máx 200)

---

### `get_stats`
Retorna contagens gerais do banco.

**Retorno exemplo:**
```json
{
  "total_vehicles": 986123,
  "total_empresas": 170456,
  "total_registrations": 1023891,
  "total_marcas": 28,
  "total_modelos": 834
}
```

---

### `top_empresas_by_registrations`
Top N empresas por volume de compras.

**Parâmetros:**
- `year` (int, obrigatório)
- `uf` (str, opcional)
- `limit` (int, padrão 10, máx 50)

---

### `count_empresa_registrations`
Conta emplacamentos de uma empresa específica.

**Parâmetros:**
- `empresa_nome` (str, obrigatório)
- `year` (int, opcional)

---

### `get_market_share`
Market share de marcas por número de emplacamentos.

**Parâmetros:**
- `year` (int, obrigatório)
- `uf` (str, opcional)
- `segmento` (str, opcional)

**Retorno exemplo:**
```json
[
  { "marca": "MARCA_A", "total": 12340, "share_pct": 18.2 },
  { "marca": "MARCA_B", "total": 11200, "share_pct": 16.5 }
]
```

---

## 7. Pipeline de Dados

### 7.1 Carga Inicial (uma vez)

```
API Externa de Emplacamentos
  │  date_range=90  (máximo por request)
  │  date_type=emplacamento
  │  Paginação: 1000 registros/página
  ▼
sync_from_api.py --mode full --date-range 90
  │  Loop de páginas até pages_total
  │  Upsert por chassi (veículos) e CNPJ (empresas)
  │  Commit a cada 500 registros
  ▼
PostgreSQL (carga completa ~1M registros)
  │
  ▼
scripts/create_indexes.sql (executar após carga)
```

### 7.2 Sync Incremental Diário

```
Task Agendada / Cron (03:00 UTC)
  ▼
sync_from_api.py --mode incremental --days 7
  │  date_type=atualizacao (captura retroativos)
  │  Overlap de 7 dias para segurança
  │  Warm-up da API (timeout 60s)
  │  MAX_RETRIES=3 com backoff exponencial
  ▼
Upsert idempotente
  │  vehicles:      ON CONFLICT (chassi)
  │  empresas:      ON CONFLICT (cnpj)
  │  registrations: ON CONFLICT (vehicle_id, data_emplacamento)
  ▼
sync_logs: registro do resultado
```

---

## 8. Decisões de Design

### Por que PostgreSQL local em vez de cloud?

| Critério | PostgreSQL Local | Supabase Free |
|----------|-----------------|---------------|
| Volume suportado | Ilimitado | 500MB (esgotado com 1M registros) |
| Conexões simultâneas | Ilimitadas | 60 (compartilhadas) |
| Latência de query | ~1ms (local) | ~80-200ms (rede) |
| Custo | $0 | $0 / $25 (pro) |
| Controle de schema | Total | Parcial |

### Por que Cloudflare Tunnel em vez de VPS?

| Critério | Cloudflare Tunnel | VPS Dedicada |
|----------|-----------------|--------------|
| Custo | $0 | ~$20-50/mês |
| Latência adicional | ~20ms (edge SP) | Depende do datacenter |
| Manutenção | Zero | Alta |
| TLS/HTTPS | Automático | Manual |
| URL estável | Sim (domínio próprio) | Sim (IP fixo) |
| Disponibilidade | Depende do host estar ligado | 24/7 |

**Trade-off aceito**: disponível enquanto o desktop está ligado. Migração para VPS é trivial — apenas mudar `DATABASE_URL`.

### Por que Streamable HTTP em vez de stdio?

O transport `stdio` do MCP só funciona com processos locais (filho do agente). O **Streamable HTTP** permite acesso remoto de qualquer agente via URL pública.

### Por que asyncpg em vez de psycopg2?

asyncpg é 3-5x mais rápido em operações async e é o driver recomendado para SQLAlchemy 2.x em ambientes asyncio. Sem overhead de thread pool.

---

## 9. Infraestrutura Windows

### Serviços em execução

| Serviço | Como rodar | Porta |
|---------|-----------|-------|
| PostgreSQL 16 | Docker Desktop | 5432 |
| Redis 7 | Docker Desktop | 6379 |
| Redis Commander | Docker Desktop | 8081 |
| MCP Server | `.venv\Scripts\python.exe -m mcp_server.main` | 8888 |
| Cloudflare Tunnel | `cloudflared tunnel --config infra/cloudflare-tunnel.yml run` | — |

### Inicialização automática (opcional)

```powershell
# Cloudflared como serviço Windows (recomendado)
cloudflared service install --config "C:\...\fleetintel-mcp\infra\cloudflare-tunnel.yml"
net start cloudflared
```

---

## 10. Roadmap Técnico

| Prioridade | Item | Impacto |
|-----------|------|---------|
| Alta | Busca semântica por empresa (pgvector) | Consultas em linguagem natural mais precisa |
| Alta | Migração para VPS dedicada | Disponibilidade 24/7 |
| Média | Cache Redis com TTL por tool | Reduz latência em perguntas repetidas |
| Média | Tool `compare_empresas` | Análise comparativa entre 2+ empresas |
| Baixa | Dashboard de monitoramento | Visibilidade de uso e performance |

---

*Documento mantido por Guilherme Taitson — atualizado em março/2026*
